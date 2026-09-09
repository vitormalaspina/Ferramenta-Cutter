import os
from pathlib import Path
import stat

ROOT = Path("/home/vitor/Ferramentas/youtube-cutter")
BACKEND = ROOT / "backend"

FILES = {}

FILES["requirements.txt"] = """fastapi>=0.111.0
uvicorn[standard]>=0.29.0
sqlalchemy>=2.0.0
alembic>=1.13.0
pydantic>=2.7.0
yt-dlp>=2024.1.0
python-multipart>=0.0.9
aiofiles>=23.2.1
httpx>=0.27.0
python-dotenv>=1.0.0
fastapi-utils>=0.7.0
"""

FILES["api/__init__.py"] = ""
FILES["models/__init__.py"] = ""
FILES["services/__init__.py"] = ""
FILES["workers/__init__.py"] = ""
FILES["utils/__init__.py"] = ""

FILES["utils/sanitize.py"] = """import re

def sanitize_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\\\|?*]', '', name)
    return name.strip()[:100]
"""

FILES["utils/duration.py"] = """def parse_duration(s: str) -> int:
    if not s: return 0
    parts = str(s).split(':')
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    elif len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    else:
        return int(parts[0])

def format_duration(seconds: int) -> str:
    if seconds is None: return "0:00"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0: return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

def calculate_clips(total_seconds: int, clip_seconds: int, keep_last: bool) -> list:
    clips = []
    if total_seconds <= 0 or clip_seconds <= 0: return clips
    start = 0
    idx = 1
    while start + clip_seconds <= total_seconds:
        clips.append({"start": start, "end": start + clip_seconds, "index": idx})
        start += clip_seconds
        idx += 1
    remaining = total_seconds - start
    if remaining > 0 and keep_last:
        clips.append({"start": start, "end": total_seconds, "index": idx})
    return clips
"""

FILES["utils/logger.py"] = """import logging
import sys
from pathlib import Path

LOGS_DIR = Path("/home/vitor/Ferramentas/youtube-cutter/logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS_DIR / "app.log"

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh = logging.FileHandler(LOG_FILE)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger
"""

FILES["models/database.py"] = """from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from pathlib import Path
import datetime
import uuid

DB_PATH = Path("/home/vitor/Ferramentas/youtube-cutter/storage/jobs/youtube_cutter.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Source(Base):
    __tablename__ = "sources"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    url = Column(String, unique=True, index=True)
    source_type = Column(String)
    channel_name = Column(String)
    channel_avatar = Column(String)
    total_videos = Column(Integer)
    metadata_json = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime)

class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    source_url = Column(String)
    source_type = Column(String)
    source_id = Column(String)
    channel_name = Column(String)
    config_json = Column(Text)
    progress_json = Column(Text)
    output_dir = Column(String)
    zip_path = Column(String)
    error_msg = Column(Text, nullable=True)
    videos = relationship("JobVideo", back_populates="job", cascade="all, delete-orphan")

class JobVideo(Base):
    __tablename__ = "job_videos"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("jobs.id"))
    video_id = Column(String)
    video_title = Column(String)
    video_url = Column(String)
    status = Column(String, default="pending")
    clips_total = Column(Integer, default=0)
    clips_done = Column(Integer, default=0)
    error_msg = Column(Text, nullable=True)
    output_dir = Column(String)
    job = relationship("Job", back_populates="videos")

Base.metadata.create_all(bind=engine)
"""

FILES["models/schemas.py"] = """from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class AnalyzeRequest(BaseModel):
    url: str

class VideoSchema(BaseModel):
    id: str
    title: str
    url: str
    thumbnail: str
    duration_seconds: int
    duration_formatted: str
    published_at: str
    view_count: int

class AnalyzeResponse(BaseModel):
    source_id: str
    source_type: str
    channel_name: str
    channel_avatar: Optional[str]
    total_videos: int
    videos: List[VideoSchema]
    page: int
    total_pages: int

class JobConfigRequest(BaseModel):
    source_id: str
    selected_video_ids: List[str]
    clip_mode: str = "duration"
    clip_duration_seconds: int = 90
    keep_last_clip: bool = True
    output_format: str = "9:16"
    resolution: str = "1080x1920"
    framing: str = "center"
    zoom_enabled: bool = False
    zoom_intensity: int = 10
    zoom_mode: str = "fixed"
    subtitles_enabled: bool = False
    subtitle_language: str = "pt"
    subtitle_font_size: int = 48
    subtitle_position: str = "bottom"
    subtitle_words_per_line: int = 4
    audio_mode: str = "keep"
    fps: str = "original"
    quality: str = "auto"
    codec: str = "h264"
    concurrent_jobs: int = 2
    best_moments_count: int = 5
    best_moments_min_duration: int = 30
    best_moments_max_duration: int = 90
    best_moments_style: str = "auto"

class VideoError(BaseModel):
    video_id: str
    title: str
    error: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    source_url: str
    channel_name: Optional[str]
    total_videos: int
    videos_done: int
    current_video_title: Optional[str]
    current_video_index: int
    total_clips: int
    clips_done: int
    current_clip_index: int
    current_clip_total: int
    progress_percent: int
    estimated_seconds_remaining: int
    output_path: Optional[str]
    zip_path: Optional[str]
    zip_size_bytes: Optional[int]
    error_msg: Optional[str]
    video_errors: List[VideoError]
"""

FILES["services/youtube_service.py"] = """import yt_dlp
import json
import uuid
import math
from datetime import datetime
from models.database import SessionLocal, Source
from models.schemas import AnalyzeResponse, VideoSchema
from utils.duration import format_duration
from utils.logger import get_logger

logger = get_logger(__name__)

class VideoUnavailableError(Exception): pass
class ChannelNotFoundError(Exception): pass
class InvalidURLError(Exception): pass

class YouTubeService:
    @staticmethod
    def analyze_url(url: str) -> dict:
        ydl_opts = {
            'extract_flat': True,
            'quiet': True,
            'no_warnings': True,
            'playlistend': 0, # Fetch all entries metadata
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as e:
            logger.error(f"yt-dlp error: {e}")
            raise InvalidURLError("Failed to fetch info. URL may be invalid.")

        if not info:
            raise InvalidURLError("No info found")
            
        source_type = "video"
        if 'entries' in info:
            source_type = "playlist" if 'playlist' in info.get('webpage_url_basename', '') else "channel"

        entries = info.get('entries', [info]) if 'entries' in info else [info]
        videos = []
        for entry in entries:
            if not entry: continue
            videos.append({
                "id": entry.get('id', ''),
                "title": entry.get('title', 'Unknown'),
                "url": entry.get('url', f"https://youtube.com/watch?v={entry.get('id')}"),
                "thumbnail": entry.get('thumbnail', ''),
                "duration_seconds": entry.get('duration', 0),
                "duration_formatted": format_duration(entry.get('duration', 0)),
                "published_at": entry.get('upload_date', 'Unknown'),
                "view_count": entry.get('view_count', 0)
            })

        source_id = str(uuid.uuid4())
        channel_name = info.get('uploader', info.get('channel', 'Unknown'))
        channel_avatar = info.get('thumbnail', '') if source_type == 'channel' else ''

        db = SessionLocal()
        source = Source(
            id=source_id,
            url=url,
            source_type=source_type,
            channel_name=channel_name,
            channel_avatar=channel_avatar,
            total_videos=len(videos),
            metadata_json=json.dumps(videos)
        )
        db.add(source)
        db.commit()
        db.close()
        
        return YouTubeService.get_videos(source_id, 1)

    @staticmethod
    def get_videos(source_id: str, page: int = 1, search: str = "", sort: str = "date") -> dict:
        db = SessionLocal()
        source = db.query(Source).filter(Source.id == source_id).first()
        db.close()
        
        if not source:
            raise ChannelNotFoundError("Source not found")
            
        all_videos = json.loads(source.metadata_json)
        
        if search:
            all_videos = [v for v in all_videos if search.lower() in v['title'].lower()]
            
        if sort == "date":
            # Just relying on original order or string sorting
            pass
        
        per_page = 20
        total = len(all_videos)
        total_pages = math.ceil(total / per_page)
        
        start = (page - 1) * per_page
        end = start + per_page
        
        paginated = all_videos[start:end]
        
        return {
            "source_id": source_id,
            "source_type": source.source_type,
            "channel_name": source.channel_name,
            "channel_avatar": source.channel_avatar,
            "total_videos": total,
            "videos": paginated,
            "page": page,
            "total_pages": total_pages
        }

    @staticmethod
    def download_video(video_url: str, output_path: str, progress_callback) -> str:
        def my_hook(d):
            if d['status'] == 'downloading':
                try:
                    percent_str = d['_percent_str']
                    percent = float(percent_str.replace('%','').strip())
                    progress_callback(percent)
                except:
                    pass
            elif d['status'] == 'finished':
                progress_callback(100)

        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_path,
            'progress_hooks': [my_hook],
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4'
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            return output_path
        except Exception as e:
            logger.error(f"Download error: {e}")
            raise VideoUnavailableError(f"Failed to download {video_url}: {str(e)}")
"""

FILES["services/ffmpeg_service.py"] = """import subprocess
import json
import re
from dataclasses import dataclass
from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class ProcessOptions:
    output_format: str = 'original'
    resolution: str = 'auto'
    fps: str = 'original'
    quality: str = 'auto'
    codec: str = 'h264'
    audio_mode: str = 'keep'
    zoom_enabled: bool = False
    zoom_intensity: int = 10
    zoom_mode: str = 'fixed'

class FFmpegService:
    @staticmethod
    def get_video_info(path: str) -> dict:
        cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', path]
        try:
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            data = json.loads(out)
            video_stream = next((s for s in data.get('streams', []) if s['codec_type'] == 'video'), None)
            if not video_stream: return {}
            
            return {
                'duration': float(data.get('format', {}).get('duration', 0)),
                'width': int(video_stream.get('width', 0)),
                'height': int(video_stream.get('height', 0)),
                'fps': eval(video_stream.get('r_frame_rate', '0/1'))
            }
        except Exception as e:
            logger.error(f"ffprobe error: {e}")
            return {}

    @staticmethod
    def build_filter_complex(options: ProcessOptions) -> str:
        filters = []
        if options.output_format == '9:16':
            filters.append("scale=-1:1920,crop=1080:1920")
        elif options.output_format == '1:1':
            filters.append("crop=min(iw\\,ih):min(iw\\,ih),scale=1080:1080")
        return ",".join(filters) if filters else ""

    @staticmethod
    def process_clip(input_path: str, output_path: str, start_sec: int, end_sec: int, options: ProcessOptions, progress_callback):
        duration = end_sec - start_sec
        cmd = [
            'ffmpeg', '-y', 
            '-ss', str(start_sec),
            '-i', input_path,
            '-t', str(duration)
        ]
        
        vf = FFmpegService.build_filter_complex(options)
        if vf: cmd.extend(['-vf', vf])
            
        if options.audio_mode == 'remove':
            cmd.append('-an')
            
        cmd.extend(['-c:v', 'libx264', '-preset', 'fast', output_path])
        
        process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True)
        time_regex = re.compile(r"time=(\d+):(\d+):(\d+.\d+)")
        
        for line in process.stderr:
            match = time_regex.search(line)
            if match:
                h, m, s = match.groups()
                current_time = int(h)*3600 + int(m)*60 + float(s)
                percent = min(100, int((current_time / duration) * 100))
                if progress_callback:
                    progress_callback(percent)
                    
        process.wait()
        if progress_callback:
            progress_callback(100)
            
    @staticmethod
    def cut_clip(input_path: str, output_path: str, start_sec: int, end_sec: int, options: ProcessOptions):
        FFmpegService.process_clip(input_path, output_path, start_sec, end_sec, options, None)
"""

FILES["services/zip_service.py"] = """import shutil
from pathlib import Path
import os

class ZipService:
    @staticmethod
    def create_zip(job_id: str, clips_dir: str, output_path: str) -> str:
        base_name = output_path.replace('.zip', '')
        shutil.make_archive(base_name, 'zip', clips_dir)
        return output_path

    @staticmethod
    def estimate_size(directory: str) -> int:
        total = 0
        for dirpath, _, filenames in os.walk(directory):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total += os.path.getsize(fp)
        return total
"""

FILES["services/disk_service.py"] = """import shutil

class DiskService:
    @staticmethod
    def get_available_space(path: str) -> int:
        total, used, free = shutil.disk_usage(path)
        return free

    @staticmethod
    def estimate_required_space(videos: list, options: dict) -> int:
        return 1024 * 1024 * 1024 * len(videos) # Rough estimate: 1GB per video

    @staticmethod
    def check_space(path: str, required_bytes: int) -> tuple:
        available = DiskService.get_available_space(path)
        return (available >= required_bytes, available, required_bytes)
"""

FILES["services/job_service.py"] = """from models.database import SessionLocal, Job, JobVideo
import json

class JobService:
    @staticmethod
    def create_job(job_data: dict, videos_data: list) -> Job:
        db = SessionLocal()
        job = Job(
            source_url=job_data.get('source_url', ''),
            source_id=job_data.get('source_id', ''),
            source_type=job_data.get('source_type', 'channel'),
            channel_name=job_data.get('channel_name', ''),
            config_json=json.dumps(job_data.get('config', {})),
            progress_json=json.dumps({}),
            output_dir=job_data.get('output_dir', '')
        )
        db.add(job)
        db.flush()
        
        for v in videos_data:
            jv = JobVideo(
                job_id=job.id,
                video_id=v['id'],
                video_title=v['title'],
                video_url=v['url'],
                output_dir=f"{job.output_dir}/{v['id']}"
            )
            db.add(jv)
            
        db.commit()
        db.refresh(job)
        db.close()
        return job

    @staticmethod
    def get_job(job_id: str) -> Job:
        db = SessionLocal()
        job = db.query(Job).filter(Job.id == job_id).first()
        db.close()
        return job

    @staticmethod
    def update_job_status(job_id: str, status: str, progress: dict = None, error: str = None):
        db = SessionLocal()
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = status
            if progress: job.progress_json = json.dumps(progress)
            if error: job.error_msg = error
            db.commit()
        db.close()
"""

FILES["services/transcription_service.py"] = """class TranscriptionService:
    async def transcribe(self, audio_path: str, language: str) -> list:
        # Returns: [{"start": 0.0, "end": 2.5, "text": "..."}]
        # NOT IMPLEMENTED - requires Whisper
        raise NotImplementedError("Whisper not configured")
"""

FILES["services/ai_clip_analyzer.py"] = """class AIClipAnalyzer:
    async def find_best_moments(self, transcript, count, min_dur, max_dur, style) -> list:
        # Returns: [{"start_sec": 30, "end_sec": 90, "score": 0.95, "reason": "..."}]
        # NOT IMPLEMENTED - plug in OpenAI/local model here
        raise NotImplementedError("AI analyzer not configured")
"""

FILES["services/subtitle_service.py"] = """class SubtitleService:
    def generate_srt(self, segments, words_per_line) -> str:
        # Generates SRT from transcription segments
        pass
    
    def burn_subtitles(self, input_path, srt_path, output_path, options) -> None:
        # Burns subtitles via FFmpeg
        pass
"""

FILES["services/video_service.py"] = """import os
from pathlib import Path
from services.youtube_service import YouTubeService
from services.ffmpeg_service import FFmpegService, ProcessOptions
from utils.duration import calculate_clips
from utils.sanitize import sanitize_filename
from utils.logger import get_logger

logger = get_logger(__name__)

async def process_video(job_id: str, video: dict, config: dict, output_dir: str, progress_cb, cancel_event):
    if cancel_event and cancel_event.is_set(): return
    
    out_dir = Path(output_dir) / sanitize_filename(f"Video_{video.get('title', video.get('id', 'Unknown'))}")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    temp_dl = out_dir / "full_video.mp4"
    
    def dl_progress(p):
        progress_cb('download', p)
        
    logger.info(f"Downloading {video['url']}")
    YouTubeService.download_video(video['url'], str(temp_dl), dl_progress)
    
    info = FFmpegService.get_video_info(str(temp_dl))
    duration = info.get('duration', video.get('duration_seconds', 0))
    
    clips = calculate_clips(duration, config.get('clip_duration_seconds', 90), config.get('keep_last_clip', True))
    total_clips = len(clips)
    
    opts = ProcessOptions(
        output_format=config.get('output_format', 'original'),
        resolution=config.get('resolution', 'auto')
    )
    
    for i, clip in enumerate(clips):
        if cancel_event and cancel_event.is_set(): break
        
        clip_out = out_dir / f"corte_{clip['index']:03d}.mp4"
        def clip_progress(p):
            progress_cb('clip', p, i+1, total_clips)
            
        FFmpegService.process_clip(str(temp_dl), str(clip_out), int(clip['start']), int(clip['end']), opts, clip_progress)
        
    try:
        os.remove(temp_dl)
    except:
        pass
"""

FILES["workers/job_worker.py"] = """import asyncio
import json
from pathlib import Path
from services.job_service import JobService
from services.video_service import process_video
from utils.logger import get_logger

logger = get_logger(__name__)

active_jobs = {}
job_events = {}

class JobEventBroadcaster:
    def __init__(self):
        self.queues = []
    def add_queue(self, q):
        self.queues.append(q)
    def remove_queue(self, q):
        if q in self.queues:
            self.queues.remove(q)
    async def broadcast(self, data: dict):
        for q in self.queues:
            await q.put(data)

def get_broadcaster(job_id: str):
    if job_id not in job_events:
        job_events[job_id] = JobEventBroadcaster()
    return job_events[job_id]

async def run_job(job_id: str):
    job = JobService.get_job(job_id)
    if not job: return
    
    cancel_event = asyncio.Event()
    active_jobs[job_id] = cancel_event
    broadcaster = get_broadcaster(job_id)
    
    try:
        JobService.update_job_status(job_id, "processing")
        await broadcaster.broadcast({"type": "progress", "job_id": job_id, "status": "processing"})
        
        config = json.loads(job.config_json)
        videos = job.videos
        
        for idx, video in enumerate(videos):
            if cancel_event.is_set(): break
            
            await broadcaster.broadcast({
                "type": "video_start", 
                "video_index": idx+1, 
                "video_title": video.video_title
            })
            
            def progress_cb(stage, p, c_idx=0, c_total=0):
                if stage == 'clip':
                    asyncio.create_task(broadcaster.broadcast({
                        "type": "clip_progress",
                        "clip_index": c_idx,
                        "clip_total": c_total,
                        "percent": p
                    }))
                    
            await process_video(job_id, {"id": video.video_id, "url": video.video_url, "title": video.video_title}, config, job.output_dir, progress_cb, cancel_event)
            
            await broadcaster.broadcast({
                "type": "video_done",
                "video_index": idx+1,
                "clips_generated": getattr(video, 'clips_total', 0)
            })
            
        if cancel_event.is_set():
            JobService.update_job_status(job_id, "cancelled")
            await broadcaster.broadcast({"type": "cancelled"})
        else:
            JobService.update_job_status(job_id, "completed")
            await broadcaster.broadcast({"type": "completed"})
            
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        JobService.update_job_status(job_id, "failed", error=str(e))
        await broadcaster.broadcast({"type": "failed", "error": str(e)})
    finally:
        if job_id in active_jobs:
            del active_jobs[job_id]
"""

FILES["api/routes/analyze.py"] = """from fastapi import APIRouter, HTTPException, Query
from models.schemas import AnalyzeRequest, AnalyzeResponse
from services.youtube_service import YouTubeService

router = APIRouter()

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_url(req: AnalyzeRequest):
    try:
        return YouTubeService.analyze_url(req.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/videos/{source_id}")
async def get_videos(source_id: str, page: int = 1, search: str = "", sort: str = "date"):
    try:
        return YouTubeService.get_videos(source_id, page, search, sort)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
"""

FILES["api/routes/jobs.py"] = """from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse, FileResponse
from models.schemas import JobConfigRequest, JobStatusResponse
from services.job_service import JobService
from services.youtube_service import YouTubeService
from services.zip_service import ZipService
from workers.job_worker import run_job, get_broadcaster, active_jobs
import json
import asyncio
from pathlib import Path

router = APIRouter()
OUTPUT_DIR = Path("/home/vitor/Ferramentas/youtube-cutter/storage/output")
TEMP_DIR = Path("/home/vitor/Ferramentas/youtube-cutter/storage/temp")

@router.post("")
async def create_job(req: JobConfigRequest, bg_tasks: BackgroundTasks):
    try:
        source_data = YouTubeService.get_videos(req.source_id, 1) # fetch for metadata
        videos_to_process = [v for v in source_data['videos'] if v['id'] in req.selected_video_ids]
        
        job_data = {
            "source_id": req.source_id,
            "source_type": source_data['source_type'],
            "source_url": f"https://youtube.com/{req.source_id}",
            "channel_name": source_data['channel_name'],
            "config": req.model_dump(),
            "output_dir": str(OUTPUT_DIR / "temp_job")
        }
        
        job = JobService.create_job(job_data, videos_to_process)
        job.output_dir = str(OUTPUT_DIR / job.id)
        JobService.update_job_status(job.id, "pending")
        
        bg_tasks.add_task(run_job, job.id)
        return {"job_id": job.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("")
async def list_jobs():
    from models.database import SessionLocal, Job
    db = SessionLocal()
    jobs = db.query(Job).all()
    db.close()
    return [{"job_id": j.id, "status": j.status} for j in jobs]

@router.get("/{job_id}")
async def get_job_status(job_id: str):
    job = JobService.get_job(job_id)
    if not job: raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job.id,
        "status": job.status,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "source_url": job.source_url,
        "channel_name": job.channel_name,
        "total_videos": len(job.videos),
        "videos_done": 0,
        "current_video_title": None,
        "current_video_index": 0,
        "total_clips": 0,
        "clips_done": 0,
        "current_clip_index": 0,
        "current_clip_total": 0,
        "progress_percent": 0,
        "estimated_seconds_remaining": 0,
        "output_path": job.output_dir,
        "zip_path": job.zip_path,
        "zip_size_bytes": None,
        "error_msg": job.error_msg,
        "video_errors": []
    }

@router.get("/{job_id}/events")
async def job_events(job_id: str, request: Request):
    broadcaster = get_broadcaster(job_id)
    q = asyncio.Queue()
    broadcaster.add_queue(q)
    
    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                data = await q.get()
                yield f"data: {json.dumps(data)}\\n\\n"
        finally:
            broadcaster.remove_queue(q)
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.delete("/{job_id}")
async def cancel_job(job_id: str):
    if job_id in active_jobs:
        active_jobs[job_id].set()
    JobService.update_job_status(job_id, "cancelled")
    return {"status": "cancelled"}

@router.post("/{job_id}/zip")
async def generate_zip(job_id: str):
    job = JobService.get_job(job_id)
    if not job: raise HTTPException(status_code=404, detail="Job not found")
    
    zip_path = str(TEMP_DIR / f"{job_id}.zip")
    ZipService.create_zip(job_id, job.output_dir, zip_path)
    
    from models.database import SessionLocal, Job
    db = SessionLocal()
    j = db.query(Job).filter(Job.id == job_id).first()
    j.zip_path = zip_path
    db.commit()
    db.close()
    
    return {"zip_path": zip_path}

@router.get("/{job_id}/download")
async def download_zip(job_id: str):
    job = JobService.get_job(job_id)
    if not job or not job.zip_path:
        raise HTTPException(status_code=404, detail="ZIP not found")
    return FileResponse(job.zip_path, filename=f"youtube_cutter_{job_id}.zip")

@router.delete("/{job_id}/files")
async def cleanup_files(job_id: str):
    job = JobService.get_job(job_id)
    if not job: return {"status": "ok"}
    import shutil
    try:
        if job.output_dir and Path(job.output_dir).exists():
            shutil.rmtree(job.output_dir)
        if job.zip_path and Path(job.zip_path).exists():
            Path(job.zip_path).unlink()
    except Exception as e:
        pass
    return {"status": "ok"}
"""

FILES["api/routes/health.py"] = """from fastapi import APIRouter
import subprocess
from services.disk_service import DiskService
import yt_dlp

router = APIRouter()

@router.get("/health")
async def health_check():
    ffmpeg_ok = False
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ffmpeg_ok = True
    except: pass
    
    disk_space = DiskService.get_available_space("/")
    
    return {
        "status": "ok",
        "ffmpeg_available": ffmpeg_ok,
        "ytdlp_version": yt_dlp.version.__version__,
        "disk_space_bytes": disk_space
    }
"""

FILES["main.py"] = """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import analyze, jobs, health

app = FastAPI(title="YouTube Cutter", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(analyze.router, prefix="/api", tags=["Analyze"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])

@app.on_event("startup")
async def startup_event():
    import models.database
    print("Database initialized")
"""

for filepath, content in FILES.items():
    full_path = BACKEND / filepath
    full_path.parent.mkdir(parents=True, exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Backend files generated successfully.")
