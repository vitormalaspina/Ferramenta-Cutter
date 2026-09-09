from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime


class AnalyzeRequest(BaseModel):
    url: str


class VideoSchema(BaseModel):
    id: str
    title: str
    url: str
    thumbnail: Optional[str] = ""
    duration_seconds: int = 0
    duration_formatted: str = "0:00"
    published_at: Optional[str] = None
    view_count: Optional[int] = 0


class AnalyzeResponse(BaseModel):
    source_id: str
    source_type: str
    channel_name: Optional[str] = "Canal"
    channel_avatar: Optional[str] = None
    total_videos: int = 0
    videos: List[VideoSchema]
    page: int = 1
    total_pages: int = 1


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
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    source_url: str = ""
    channel_name: Optional[str] = None
    total_videos: int = 0
    videos_done: int = 0
    current_video_title: Optional[str] = None
    current_video_index: int = 0
    total_clips: int = 0
    clips_done: int = 0
    current_clip_index: int = 0
    current_clip_total: int = 0
    progress_percent: int = 0
    estimated_seconds_remaining: Optional[int] = None
    output_path: Optional[str] = None
    zip_path: Optional[str] = None
    zip_size_bytes: Optional[int] = None
    error_msg: Optional[str] = None
    video_errors: List[VideoError] = []
