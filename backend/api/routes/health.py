from fastapi import APIRouter
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
