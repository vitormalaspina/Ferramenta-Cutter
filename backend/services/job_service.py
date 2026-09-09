import json
import datetime
from pathlib import Path
from models.database import SessionLocal, Job, JobVideo
from utils.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class JobService:
    @staticmethod
    def create_job(job_data: dict, videos_data: list) -> Job:
        db = SessionLocal()
        try:
            job = Job(
                source_url=job_data.get("source_url", ""),
                source_id=job_data.get("source_id", ""),
                source_type=job_data.get("source_type", "channel"),
                channel_name=job_data.get("channel_name", ""),
                config_json=json.dumps(job_data.get("config", {})),
                progress_json=json.dumps({}),
                output_dir="",  # set after we know the job id
            )
            db.add(job)
            db.flush()  # get job.id

            # Set output dir now that we have the id
            output_dir = str(settings.output_dir / job.id)
            job.output_dir = output_dir

            for v in videos_data:
                jv = JobVideo(
                    job_id=job.id,
                    video_id=v.get("id", ""),
                    video_title=v.get("title", "Unknown"),
                    video_url=v.get("url", ""),
                    duration_seconds=int(v.get("duration_seconds") or 0),
                    output_dir=str(Path(output_dir) / v.get("id", "unknown")),
                )
                db.add(jv)

            db.commit()
            db.refresh(job)
            return job
        finally:
            db.close()

    @staticmethod
    def get_job(job_id: str) -> Job | None:
        db = SessionLocal()
        try:
            return db.query(Job).filter(Job.id == job_id).first()
        finally:
            db.close()

    @staticmethod
    def get_job_info_dict(job_id: str) -> dict | None:
        """
        Returns job info as a plain dict INCLUDING videos as plain dicts.
        Must be used by the job worker to avoid DetachedInstanceError when
        the session is closed before accessing job.videos.
        """
        db = SessionLocal()
        try:
            j = db.query(Job).filter(Job.id == job_id).first()
            if not j:
                return None
            videos = [
                {
                    "video_id": v.video_id,
                    "video_title": v.video_title,
                    "video_url": v.video_url,
                    "duration_seconds": v.duration_seconds or 0,
                    "output_dir": v.output_dir,
                }
                for v in j.videos
            ]
            return {
                "id": j.id,
                "config_json": j.config_json,
                "output_dir": j.output_dir,
                "source_url": j.source_url,
                "channel_name": j.channel_name,
                "videos": videos,
            }
        finally:
            db.close()

    @staticmethod
    def get_total_clips(job_id: str) -> int:
        """Returns sum of clips_total across all videos for a job."""
        db = SessionLocal()
        try:
            videos = db.query(JobVideo).filter(JobVideo.job_id == job_id).all()
            return sum(v.clips_total or 0 for v in videos)
        finally:
            db.close()

    @staticmethod
    def list_jobs() -> list[dict]:
        db = SessionLocal()
        try:
            jobs = db.query(Job).order_by(Job.created_at.desc()).all()
            result = []
            for j in jobs:
                config = {}
                try:
                    config = json.loads(j.config_json or "{}")
                except Exception:
                    pass
                progress = {}
                try:
                    progress = json.loads(j.progress_json or "{}")
                except Exception:
                    pass

                result.append({
                    "job_id": j.id,
                    "status": j.status,
                    "created_at": j.created_at.isoformat() if j.created_at else None,
                    "updated_at": j.updated_at.isoformat() if j.updated_at else None,
                    "source_url": j.source_url or "",
                    "source_type": j.source_type,
                    "channel_name": j.channel_name,
                    "total_videos": len(j.videos),
                    "total_clips": progress.get("total_clips", 0),
                    "output_format": config.get("output_format", "original"),
                    "subtitles_enabled": config.get("subtitles_enabled", False),
                    "zip_path": j.zip_path,
                    "zip_size_bytes": j.zip_size_bytes,
                    "error_msg": j.error_msg,
                })
            return result
        finally:
            db.close()

    @staticmethod
    def get_job_detail(job_id: str) -> dict | None:
        db = SessionLocal()
        try:
            j = db.query(Job).filter(Job.id == job_id).first()
            if not j:
                return None

            progress = {}
            try:
                progress = json.loads(j.progress_json or "{}")
            except Exception:
                pass

            video_errors = [
                {"video_id": v.video_id, "title": v.video_title, "error": v.error_msg}
                for v in j.videos
                if v.error_msg
            ]

            videos_done = sum(1 for v in j.videos if v.status in ("done", "error"))
            total_clips = sum(v.clips_total or 0 for v in j.videos)
            clips_done = sum(v.clips_done or 0 for v in j.videos)

            return {
                "job_id": j.id,
                "status": j.status,
                "created_at": j.created_at.isoformat() if j.created_at else None,
                "updated_at": j.updated_at.isoformat() if j.updated_at else None,
                "source_url": j.source_url or "",
                "channel_name": j.channel_name,
                "total_videos": len(j.videos),
                "videos_done": videos_done,
                "current_video_title": progress.get("current_video_title"),
                "current_video_index": progress.get("current_video_index", 0),
                "total_clips": total_clips,
                "clips_done": clips_done,
                "current_clip_index": progress.get("current_clip_index", 0),
                "current_clip_total": progress.get("current_clip_total", 0),
                "progress_percent": progress.get("progress_percent", 0),
                "estimated_seconds_remaining": progress.get("estimated_seconds_remaining"),
                "output_path": j.output_dir,
                "zip_path": j.zip_path,
                "zip_size_bytes": j.zip_size_bytes,
                "error_msg": j.error_msg,
                "video_errors": video_errors,
            }
        finally:
            db.close()

    @staticmethod
    def update_job_status(job_id: str, status: str, progress: dict | None = None, error: str | None = None):
        db = SessionLocal()
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.status = status
                job.updated_at = datetime.datetime.now(datetime.timezone.utc)
                if progress is not None:
                    job.progress_json = json.dumps(progress)
                if error is not None:
                    job.error_msg = error
                db.commit()
        except Exception as e:
            logger.error(f"Failed to update job {job_id}: {e}")
            db.rollback()
        finally:
            db.close()

    @staticmethod
    def update_video_status(job_id: str, video_id: str, status: str,
                            clips_total: int = 0, clips_done: int = 0,
                            error: str | None = None):
        db = SessionLocal()
        try:
            video = (
                db.query(JobVideo)
                .filter(JobVideo.job_id == job_id, JobVideo.video_id == video_id)
                .first()
            )
            if video:
                video.status = status
                if clips_total:
                    video.clips_total = clips_total
                if clips_done:
                    video.clips_done = clips_done
                if error is not None:
                    video.error_msg = error
                db.commit()
        except Exception as e:
            logger.error(f"Failed to update video {video_id}: {e}")
            db.rollback()
        finally:
            db.close()

    @staticmethod
    def update_zip(job_id: str, zip_path: str, zip_size_bytes: int):
        db = SessionLocal()
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.zip_path = zip_path
                job.zip_size_bytes = zip_size_bytes
                job.updated_at = datetime.datetime.now(datetime.timezone.utc)
                db.commit()
        finally:
            db.close()

    @staticmethod
    def delete_job(job_id: str):
        db = SessionLocal()
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                db.delete(job)
                db.commit()
        finally:
            db.close()
