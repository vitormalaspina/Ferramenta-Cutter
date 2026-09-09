import yt_dlp
import json
import uuid
import math
import re
from datetime import datetime
from models.database import SessionLocal, Source
from utils.duration import format_duration
from utils.logger import get_logger

logger = get_logger(__name__)


class VideoUnavailableError(Exception):
    pass


class ChannelNotFoundError(Exception):
    pass


class InvalidURLError(Exception):
    pass


class YouTubeService:
    @staticmethod
    def analyze_url(url: str) -> dict:
        url = url.strip()
        if not url:
            raise InvalidURLError("A URL fornecida está vazia.")

        # Ensure valid YouTube URL format
        if not re.search(r'(youtube\.com|youtu\.be)', url, re.IGNORECASE):
            raise InvalidURLError("A URL fornecida não é uma URL válida do YouTube.")

        # Append /videos if it's a channel URL without specific tab to get video listing directly
        target_url = url
        if re.search(r'youtube\.com/(@[\w\.-]+|c/[\w\.-]+|channel/[\w\.-]+)$', url.rstrip('/')):
            target_url = url.rstrip('/') + '/videos'

        ydl_opts = {
            'extract_flat': True,
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(target_url, download=False)
        except Exception as e:
            logger.error(f"yt-dlp error during analysis of {url}: {e}")
            raise InvalidURLError(f"Não foi possível analisar a URL: {str(e)}")

        if not info:
            raise InvalidURLError("Nenhuma informação encontrada para esta URL.")

        # Determine source type
        source_type = "video"
        if "entries" in info:
            webpage_url = info.get("webpage_url", "") or target_url
            if "playlist" in webpage_url or "list=" in target_url:
                source_type = "playlist"
            else:
                source_type = "channel"

        raw_entries = info.get("entries", [info]) if "entries" in info else [info]
        videos = []
        for entry in raw_entries:
            if not entry or not isinstance(entry, dict):
                continue
            video_id = entry.get("id") or entry.get("url", "")
            if not video_id:
                continue

            # In flat extraction, entry.get('url') might be video id or full url
            if video_id.startswith("http"):
                video_url = video_id
            else:
                video_url = f"https://www.youtube.com/watch?v={video_id}"

            duration = int(entry.get("duration") or 0)
            upload_date = entry.get("upload_date") or ""
            formatted_date = ""
            if upload_date and len(upload_date) == 8:
                try:
                    formatted_date = f"{upload_date[6:8]}/{upload_date[4:6]}/{upload_date[0:4]}"
                except Exception:
                    formatted_date = upload_date

            thumbnail = entry.get("thumbnail") or ""
            if not thumbnail and video_id:
                thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

            availability = str(entry.get("availability") or "").lower()
            title = entry.get("title") or "Sem título"
            is_members_only = (
                availability in ("subscriber_only", "needs_auth", "premium_only")
                or "exclusivo para membros" in title.lower()
                or "members-only" in title.lower()
            )

            videos.append({
                "id": entry.get("id", video_id),
                "title": title,
                "url": video_url,
                "thumbnail": thumbnail,
                "duration_seconds": duration,
                "duration_formatted": format_duration(duration),
                "published_at": formatted_date or upload_date or None,
                "view_count": entry.get("view_count") or 0,
                "is_members_only": is_members_only,
            })

        if not videos:
            raise InvalidURLError("Nenhum vídeo foi encontrado para esta URL.")

        source_id = str(uuid.uuid4())
        channel_name = (
            info.get("uploader")
            or info.get("channel")
            or info.get("title")
            or "Canal do YouTube"
        )
        channel_avatar = info.get("thumbnail") or ""

        db = SessionLocal()
        try:
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
        finally:
            db.close()

        return YouTubeService.get_videos(source_id, page=1)

    @staticmethod
    def get_videos(source_id: str, page: int = 1, search: str = "", sort: str = "date_desc") -> dict:
        db = SessionLocal()
        try:
            source = db.query(Source).filter(Source.id == source_id).first()
            if not source:
                raise ChannelNotFoundError("Fonte de dados não encontrada.")

            all_videos = json.loads(source.metadata_json or "[]")
            channel_name = source.channel_name
            channel_avatar = source.channel_avatar
            source_type = source.source_type
        finally:
            db.close()

        # Filter by search keyword
        if search:
            query = search.lower().strip()
            all_videos = [v for v in all_videos if query in v["title"].lower()]

        # Sort
        if sort == "date_desc":
            all_videos.sort(key=lambda x: str(x.get("published_at") or ""), reverse=True)
        elif sort == "date_asc":
            all_videos.sort(key=lambda x: str(x.get("published_at") or ""))
        elif sort == "duration_desc":
            all_videos.sort(key=lambda x: x.get("duration_seconds", 0), reverse=True)
        elif sort == "duration_asc":
            all_videos.sort(key=lambda x: x.get("duration_seconds", 0))
        elif sort == "title_asc":
            all_videos.sort(key=lambda x: x.get("title", "").lower())

        per_page = 20
        total = len(all_videos)
        total_pages = max(1, math.ceil(total / per_page))
        page = max(1, min(page, total_pages))

        start = (page - 1) * per_page
        end = start + per_page
        paginated = all_videos[start:end]

        return {
            "source_id": source_id,
            "source_type": source_type,
            "channel_name": channel_name,
            "channel_avatar": channel_avatar,
            "total_videos": total,
            "videos": paginated,
            "page": page,
            "total_pages": total_pages
        }

    @staticmethod
    def download_video(video_url: str, output_path: str, progress_callback,
                       download_subtitles: bool = False, sub_lang: str = "pt") -> str:
        def my_hook(d):
            if d.get("status") == "downloading":
                try:
                    total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                    downloaded = d.get("downloaded_bytes") or 0
                    if total > 0:
                        pct = min(99, int((downloaded / total) * 100))
                        progress_callback(pct)
                    else:
                        percent_str = d.get("_percent_str", "0%").replace("%", "").strip()
                        progress_callback(float(percent_str))
                except Exception:
                    pass
            elif d.get("status") == "finished":
                progress_callback(100)

        ydl_opts = {
            # Prefer max 1080p with H.264 video + m4a audio (drastically faster download & ffmpeg decode)
            'format': (
                'bestvideo[height<=1080][vcodec^=avc1]+bestaudio[ext=m4a]/'
                'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/'
                'bestvideo[height<=1080]+bestaudio/'
                'best[height<=1080]/'
                'best'
            ),
            'outtmpl': output_path,
            'progress_hooks': [my_hook],
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4',
            'concurrent_fragment_downloads': 5,
            'buffersize': 1024 * 1024,
            'retries': 3,
            'fragment_retries': 3,
        }

        if download_subtitles:
            preferred = [sub_lang] if sub_lang and sub_lang != 'auto' else []
            preferred.extend(['pt', 'pt-BR', 'en', 'es'])
            ydl_opts.update({
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': preferred,
                'subtitlesformat': 'srt/vtt/best',
            })

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            return output_path
        except Exception as e:
            err_str = str(e)
            if "members-only" in err_str.lower() or "join this channel" in err_str.lower():
                user_msg = "Este vídeo é exclusivo para membros do canal (conteúdo pago). O YouTube exige assinatura ativa para liberar o download."
            elif "private video" in err_str.lower():
                user_msg = "Este vídeo é privado e não pode ser acessado."
            elif "copyright" in err_str.lower():
                user_msg = "Este vídeo foi bloqueado por reivindicação de direitos autorais."
            elif "sign in" in err_str.lower():
                user_msg = "O YouTube exige login para acessar este vídeo (possível restrição de idade ou membros)."
            else:
                user_msg = f"Não foi possível baixar este vídeo: {err_str}"

            logger.error(f"Download error for {video_url}: {user_msg}")
            raise VideoUnavailableError(user_msg)
