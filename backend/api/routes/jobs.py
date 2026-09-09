from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse, FileResponse
from models.schemas import JobConfigRequest
from models.database import SessionLocal, Source
from services.job_service import JobService
from services.zip_service import ZipService
from utils.config import settings
from utils.sanitize import sanitize_filename
from workers.job_worker import run_job, get_broadcaster, active_jobs
import json
import asyncio
from pathlib import Path

router = APIRouter()


@router.post("")
async def create_job(req: JobConfigRequest, bg_tasks: BackgroundTasks):
    try:
        db = SessionLocal()
        source = db.query(Source).filter(Source.id == req.source_id).first()
        db.close()

        if not source:
            raise HTTPException(status_code=404, detail="Fonte não encontrada")

        all_videos = json.loads(source.metadata_json or "[]")
        selected_set = set(req.selected_video_ids)
        videos_to_process = [v for v in all_videos if v.get("id") in selected_set]

        if not videos_to_process:
            raise HTTPException(status_code=400, detail="Nenhum vídeo válido selecionado")

        job_data = {
            "source_id": req.source_id,
            "source_type": source.source_type,
            "source_url": source.url,
            "channel_name": source.channel_name,
            "config": req.model_dump(),
        }

        job = JobService.create_job(job_data, videos_to_process)
        JobService.update_job_status(job.id, "pending")

        bg_tasks.add_task(run_job, job.id)
        return {"job_id": job.id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def list_jobs():
    return JobService.list_jobs()


@router.get("/{job_id}")
async def get_job_status(job_id: str):
    detail = JobService.get_job_detail(job_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Trabalho não encontrado")
    return detail


@router.get("/{job_id}/events")
async def job_events(job_id: str, request: Request):
    broadcaster = get_broadcaster(job_id)
    q = broadcaster.subscribe()

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(q.get(), timeout=20.0)
                    yield f"data: {json.dumps(data)}\n\n"
                except asyncio.TimeoutError:
                    # Keep-alive comment
                    yield ": keep-alive\n\n"
        finally:
            broadcaster.unsubscribe(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.delete("/{job_id}")
async def cancel_job(job_id: str):
    if job_id in active_jobs:
        active_jobs[job_id].set()
    JobService.update_job_status(job_id, "cancelled")
    return {"status": "cancelled"}


@router.post("/{job_id}/zip")
async def generate_zip(job_id: str):
    job = JobService.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Trabalho não encontrado")

    if not job.output_dir or not Path(job.output_dir).exists():
        raise HTTPException(status_code=400, detail="Diretório de saída dos cortes não encontrado")

    channel_slug = sanitize_filename(job.channel_name or "cortes")
    zip_filename = f"cortes_{channel_slug}_{job_id[:8]}.zip"
    zip_path = str(settings.output_dir / zip_filename)

    ZipService.create_zip(job_id, job.output_dir, zip_path)
    zip_size = Path(zip_path).stat().st_size if Path(zip_path).exists() else 0

    JobService.update_zip(job_id, zip_path, zip_size)
    return {"zip_path": zip_path, "zip_size_bytes": zip_size}


@router.get("/{job_id}/download")
async def download_zip(job_id: str):
    job = JobService.get_job(job_id)
    if not job or not job.zip_path or not Path(job.zip_path).exists():
        raise HTTPException(status_code=404, detail="Arquivo ZIP não encontrado ou ainda não gerado")

    channel_slug = sanitize_filename(job.channel_name or "cortes")
    filename = f"cortes_{channel_slug}_{job_id[:8]}.zip"
    return FileResponse(job.zip_path, filename=filename, media_type="application/zip")


@router.delete("/{job_id}/files")
async def cleanup_files(job_id: str):
    job = JobService.get_job(job_id)
    if not job:
        return {"status": "ok"}
    import shutil
    try:
        if job.output_dir and Path(job.output_dir).exists():
            shutil.rmtree(job.output_dir)
        if job.zip_path and Path(job.zip_path).exists():
            Path(job.zip_path).unlink()
        JobService.delete_job(job_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao excluir arquivos: {str(e)}")
    return {"status": "ok"}
