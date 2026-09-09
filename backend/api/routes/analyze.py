from fastapi import APIRouter, HTTPException, Query
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
