from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from pathlib import Path
import datetime
import uuid

# Use config for path — fallback to relative if config not available yet
try:
    from utils.config import settings
    DB_PATH = settings.db_path
except Exception:
    DB_PATH = Path(__file__).parent.parent.parent / "storage" / "jobs" / "youtube_cutter.db"

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
)
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
    url = Column(String, index=True)
    source_type = Column(String)
    channel_name = Column(String)
    channel_avatar = Column(String)
    total_videos = Column(Integer)
    metadata_json = Column(Text)  # JSON list of all video dicts
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    expires_at = Column(DateTime, nullable=True)


class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    source_url = Column(String)
    source_type = Column(String)
    source_id = Column(String)
    channel_name = Column(String)
    config_json = Column(Text)
    progress_json = Column(Text, default="{}")
    output_dir = Column(String)
    zip_path = Column(String, nullable=True)
    zip_size_bytes = Column(Integer, nullable=True)
    error_msg = Column(Text, nullable=True)
    videos = relationship("JobVideo", back_populates="job", cascade="all, delete-orphan")


class JobVideo(Base):
    __tablename__ = "job_videos"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("jobs.id"))
    video_id = Column(String)
    video_title = Column(String)
    video_url = Column(String)
    duration_seconds = Column(Integer, default=0)
    status = Column(String, default="pending")  # pending|processing|done|error
    clips_total = Column(Integer, default=0)
    clips_done = Column(Integer, default=0)
    error_msg = Column(Text, nullable=True)
    output_dir = Column(String, nullable=True)
    job = relationship("Job", back_populates="videos")
