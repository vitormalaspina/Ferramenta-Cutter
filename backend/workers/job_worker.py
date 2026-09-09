"""
Complete job worker: downloads videos, runs FFmpeg, updates progress,
broadcasts SSE events, handles cancellation.

Features:
- Live stage progress (downloading from YouTube + rendering vertical clips)
- Real-time overall percentage and dynamic ETA calculation
- SSE event throttling (max ~8 updates/sec) to avoid flooding
- Periodic DB synchronization for persistent progress on page reload
- SQLAlchemy session safety (dicts used instead of detached ORM objects)
"""
import asyncio
import json
import time
from pathlib import Path

from services.job_service import JobService
from services.video_service import process_video
from utils.logger import get_logger

logger = get_logger(__name__)

# job_id -> asyncio.Event  (set to cancel)
active_jobs: dict[str, asyncio.Event] = {}

# job_id -> JobEventBroadcaster
job_events: dict[str, "JobEventBroadcaster"] = {}


class JobEventBroadcaster:
    """Fan-out broadcaster: multiple SSE clients can subscribe to the same job."""

    def __init__(self):
        self._queues: list[asyncio.Queue] = []

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._queues.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        try:
            self._queues.remove(q)
        except ValueError:
            pass

    async def broadcast(self, data: dict):
        dead = []
        for q in self._queues:
            try:
                q.put_nowait(data)
            except asyncio.QueueFull:
                dead.append(q)
        for q in dead:
            self.unsubscribe(q)

    def has_subscribers(self) -> bool:
        return bool(self._queues)


def get_broadcaster(job_id: str) -> JobEventBroadcaster:
    if job_id not in job_events:
        job_events[job_id] = JobEventBroadcaster()
    return job_events[job_id]


def cleanup_broadcaster(job_id: str):
    job_events.pop(job_id, None)


async def run_job(job_id: str):
    """Main job runner — called as a FastAPI BackgroundTask."""
    logger.info(f"Starting job {job_id}")

    cancel_event = asyncio.Event()
    active_jobs[job_id] = cancel_event
    broadcaster = get_broadcaster(job_id)

    # ── Load job info while session is still open ─────────────
    job_info = JobService.get_job_info_dict(job_id)
    if not job_info:
        logger.error(f"Job {job_id} not found in DB")
        return

    try:
        config = json.loads(job_info["config_json"] or "{}")
        videos = job_info["videos"]  # list of plain dicts
        output_dir = job_info["output_dir"]
        total_videos = len(videos)
        start_time = time.time()

        init_progress = {
            "total_videos": total_videos,
            "videos_done": 0,
            "current_video_index": 0,
            "progress_percent": 0,
            "stage": "download",
            "stage_text": "Iniciando processamento...",
            "clip_percent": 0,
            "estimated_seconds_remaining": None,
        }
        JobService.update_job_status(job_id, "processing", progress=init_progress)
        await broadcaster.broadcast({
            "type": "progress",
            "job_id": job_id,
            "status": "processing",
            **init_progress,
        })

        videos_done = 0
        video_errors = []

        for idx, video in enumerate(videos):
            if cancel_event.is_set():
                break

            video_title = video.get("video_title") or "Vídeo"
            video_id = video.get("video_id") or ""

            await broadcaster.broadcast({
                "type": "video_start",
                "video_index": idx + 1,
                "video_total": total_videos,
                "video_title": video_title,
            })

            JobService.update_video_status(job_id, video_id, "processing")

            loop = asyncio.get_event_loop()
            last_broadcast = [0.0]
            last_db_save = [0.0]

            def make_progress_cb(v_idx: int, v_title: str):
                last_step_key = [None]

                def progress_cb(stage: str, percent: float,
                                clip_idx: int = 0, clip_total: int = 0):
                    now = time.time()

                    # Quantize into 25% steps (0%, 25%, 50%, 75%, 100%) to be ultra-lightweight
                    if percent >= 100:
                        step_pct = 100
                    elif percent >= 75:
                        step_pct = 75
                    elif percent >= 50:
                        step_pct = 50
                    elif percent >= 25:
                        step_pct = 25
                    else:
                        step_pct = 0

                    step_key = (stage, clip_idx, step_pct)
                    if step_key == last_step_key[0]:
                        return
                    last_step_key[0] = step_key

                    # ── Calculate overall percentage ──
                    video_base = (v_idx / max(1, total_videos)) * 100.0
                    video_share = 100.0 / max(1, total_videos)

                    if stage == "download":
                        # Download accounts for 20% of video's total time
                        video_pct = (step_pct / 100.0) * 20.0
                        stage_text = f"Baixando vídeo ({step_pct}%)..." if step_pct < 100 else "Download concluído"
                    else:
                        # Clip rendering accounts for remaining 80%
                        c_total = max(1, clip_total)
                        c_idx = max(1, clip_idx)
                        clip_fraction = ((c_idx - 1) + (step_pct / 100.0)) / c_total
                        video_pct = 20.0 + (clip_fraction * 80.0)
                        stage_text = f"Gerando corte {c_idx} de {c_total} ({step_pct}%)..."

                    overall_pct = min(99.0, max(0.0, video_base + (video_pct / 100.0) * video_share))

                    # ── Estimate remaining time ──
                    elapsed = now - start_time
                    est_remaining = None
                    if overall_pct > 1.5:
                        total_est = elapsed / (overall_pct / 100.0)
                        est_remaining = max(0, int(total_est - elapsed))

                    payload = {
                        "type": "progress",
                        "job_id": job_id,
                        "status": "processing",
                        "total_videos": total_videos,
                        "videos_done": videos_done,
                        "current_video_index": v_idx + 1,
                        "current_video_title": v_title,
                        "current_clip_index": clip_idx,
                        "current_clip_total": clip_total,
                        "clip_percent": step_pct,
                        "stage": stage,
                        "stage_text": stage_text,
                        "progress_percent": round(overall_pct, 1),
                        "estimated_seconds_remaining": est_remaining,
                    }

                    # Broadcast SSE event
                    coro = broadcaster.broadcast(payload)
                    asyncio.run_coroutine_threadsafe(coro, loop)

                    # Persist to DB at 100% or every ~2.5 seconds
                    if step_pct == 100 or (now - last_db_save[0] > 2.5):
                        last_db_save[0] = now
                        JobService.update_job_status(job_id, "processing", progress=payload)

                return progress_cb

            cb = make_progress_cb(idx, video_title)

            # Build video dict for process_video
            video_dict = {
                "id": video_id,
                "url": video.get("video_url") or "",
                "title": video_title,
                "duration_seconds": video.get("duration_seconds") or 0,
            }

            try:
                clips_generated = await asyncio.to_thread(
                    process_video_sync,
                    job_id,
                    video_dict,
                    config,
                    output_dir,
                    cb,
                    cancel_event,
                )

                videos_done += 1
                JobService.update_video_status(
                    job_id, video_id, "done",
                    clips_total=clips_generated, clips_done=clips_generated
                )

                elapsed = time.time() - start_time
                avg_per_video = elapsed / max(videos_done, 1)
                remaining = int(avg_per_video * (total_videos - videos_done))
                video_pct = int((videos_done / total_videos) * 100)

                progress = {
                    "total_videos": total_videos,
                    "videos_done": videos_done,
                    "current_video_index": idx + 1,
                    "current_video_title": video_title,
                    "progress_percent": video_pct,
                    "estimated_seconds_remaining": remaining if videos_done < total_videos else 0,
                    "stage_text": f"Vídeo {videos_done} de {total_videos} finalizado",
                }
                JobService.update_job_status(job_id, "processing", progress=progress)

                await broadcaster.broadcast({
                    "type": "video_done",
                    "video_index": idx + 1,
                    "video_title": video_title,
                    "clips_generated": clips_generated,
                    **progress,
                })

            except Exception as e:
                logger.error(f"Error processing video {video_id}: {e}", exc_info=True)
                error_msg = str(e)
                video_errors.append({
                    "video_id": video_id,
                    "title": video_title,
                    "error": error_msg,
                })
                JobService.update_video_status(job_id, video_id, "error", error=error_msg)
                await broadcaster.broadcast({
                    "type": "video_error",
                    "video_index": idx + 1,
                    "video_title": video_title,
                    "error": error_msg,
                })

        if cancel_event.is_set():
            logger.info(f"Job {job_id} was cancelled")
            JobService.update_job_status(job_id, "cancelled")
            await broadcaster.broadcast({"type": "cancelled", "job_id": job_id})
        elif videos_done == 0 and video_errors:
            # All selected videos failed
            first_err = video_errors[0]["error"]
            err_msg = f"Nenhum vídeo pôde ser processado. {first_err}"
            logger.error(f"Job {job_id} failed: all videos failed ({first_err})")
            JobService.update_job_status(job_id, "failed", error=err_msg)
            await broadcaster.broadcast({
                "type": "failed",
                "job_id": job_id,
                "error": err_msg,
                "video_errors": video_errors,
            })
        else:
            total_clips = JobService.get_total_clips(job_id)
            logger.info(f"Job {job_id} completed: {videos_done}/{total_videos} videos, {total_clips} clips")
            final_progress = {
                "total_videos": total_videos,
                "videos_done": videos_done,
                "total_clips": total_clips,
                "progress_percent": 100,
                "estimated_seconds_remaining": 0,
                "stage": "completed",
                "stage_text": f"Processamento concluído ({total_clips} cortes gerados)",
            }
            JobService.update_job_status(job_id, "completed", progress=final_progress)
            await broadcaster.broadcast({
                "type": "completed",
                "job_id": job_id,
                "total_videos": videos_done,
                "total_clips": total_clips,
                "video_errors": video_errors,
                **final_progress,
            })

    except Exception as e:
        logger.error(f"Job {job_id} failed with unhandled error: {e}", exc_info=True)
        JobService.update_job_status(job_id, "failed", error=str(e))
        await broadcaster.broadcast({"type": "failed", "error": str(e)})

    finally:
        active_jobs.pop(job_id, None)
        # Keep broadcaster alive briefly so SSE clients receive final event
        await asyncio.sleep(5)
        cleanup_broadcaster(job_id)


def process_video_sync(job_id: str, video: dict, config: dict,
                       output_dir: str, progress_cb, cancel_event) -> int:
    """Synchronous wrapper around video_service.process_video for asyncio.to_thread."""
    from services.video_service import process_video as _process_video
    return _process_video(job_id, video, config, output_dir, progress_cb, cancel_event)
