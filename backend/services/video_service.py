"""
video_service.py — Synchronous pipeline: download → subtitle extraction → clip generation → cleanup.
Called via asyncio.to_thread() from the job worker so it does NOT block the async event loop.
Returns the number of clips generated.
"""
from pathlib import Path

from services.youtube_service import YouTubeService
from services.ffmpeg_service import FFmpegService, ProcessOptions
from services.subtitle_service import SubtitleService
from utils.duration import calculate_clips, format_duration
from utils.sanitize import sanitize_filename
from utils.logger import get_logger

logger = get_logger(__name__)


def process_video(
    job_id: str,
    video: dict,
    config: dict,
    output_dir: str,
    progress_cb,
    cancel_event,
) -> int:
    """
    Process one video end-to-end.
    Returns the number of clips generated.
    Raises on unrecoverable errors so the worker can log/continue.
    """
    if cancel_event and cancel_event.is_set():
        return 0

    # Build output directory name: Video_01_Title_sanitized
    safe_title = sanitize_filename(video.get("title", video.get("id", "unknown")))
    out_dir = Path(output_dir) / safe_title
    out_dir.mkdir(parents=True, exist_ok=True)

    # Temporary download path
    temp_dl = out_dir / "_download_temp.mp4"

    # Subtitle config
    subtitles_enabled = bool(config.get("subtitles_enabled", False))
    sub_lang = config.get("subtitle_language", "pt")
    sub_words_per_line = int(config.get("subtitle_words_per_line", 5))
    sub_font_size = int(config.get("subtitle_font_size", 28))
    sub_position = config.get("subtitle_position", "bottom")

    # ── 1. Download Video & Subtitles ────────────────────────────
    def dl_progress(percent: float):
        progress_cb("download", percent)

    logger.info(f"[{job_id}] Downloading: {video.get('title')} (subtitles={subtitles_enabled}, lang={sub_lang})")
    YouTubeService.download_video(
        video["url"],
        str(temp_dl),
        dl_progress,
        download_subtitles=subtitles_enabled,
        sub_lang=sub_lang,
    )

    if cancel_event and cancel_event.is_set():
        _cleanup_temp_files(out_dir)
        return 0

    # ── 2. Parse Subtitles if enabled ────────────────────────────
    subtitle_cues = []
    if subtitles_enabled:
        subtitle_cues = SubtitleService.find_and_parse_subtitles(out_dir, "_download_temp")
        if subtitle_cues:
            logger.info(f"[{job_id}] Loaded {len(subtitle_cues)} subtitle cues for {video.get('title')}")
        else:
            logger.warning(f"[{job_id}] Subtitles requested but none available on YouTube for {video.get('title')}")

    # ── 3. Get actual duration via ffprobe ───────────────────────
    info = FFmpegService.get_video_info(str(temp_dl))
    duration = int(info.get("duration", 0)) or int(video.get("duration_seconds", 0))
    if duration == 0:
        logger.warning(f"[{job_id}] Could not determine duration for {video.get('title')}")

    # ── 4. Calculate clip intervals ──────────────────────────────
    clip_mode = config.get("clip_mode", "duration")
    if clip_mode == "duration":
        clip_secs = int(config.get("clip_duration_seconds", 90))
        keep_last = bool(config.get("keep_last_clip", True))
        clips = calculate_clips(duration, clip_secs, keep_last)
    else:
        # "best_moments" — fall back to duration
        logger.warning(f"[{job_id}] AI clip mode not available, using duration mode")
        clip_secs = int(config.get("clip_duration_seconds", 90))
        clips = calculate_clips(duration, clip_secs, True)

    total_clips = len(clips)
    logger.info(f"[{job_id}] {video.get('title')}: {total_clips} clips ({format_duration(duration)} total)")

    # ── 5. Generate each clip ────────────────────────────────────
    clips_done = 0
    temp_clip_subs = []

    for clip in clips:
        if cancel_event and cancel_event.is_set():
            break

        clip_idx = clip["index"]
        clip_out = out_dir / f"corte_{clip_idx:03d}.mp4"
        start_sec = int(clip["start"])
        end_sec = int(clip["end"])

        # Slice subtitles for this specific clip if available
        clip_sub_path = None
        has_clip_subs = False
        if subtitles_enabled and subtitle_cues:
            clip_sub_file = out_dir / f"_corte_{clip_idx:03d}.srt"
            has_clip_subs = SubtitleService.slice_cues_to_srt(
                subtitle_cues,
                float(start_sec),
                float(end_sec),
                clip_sub_file,
                words_per_line=sub_words_per_line,
            )
            if has_clip_subs:
                clip_sub_path = str(clip_sub_file)
                temp_clip_subs.append(clip_sub_file)

        # Build FFmpeg options for this clip
        opts = ProcessOptions(
            output_format=config.get("output_format", "original"),
            resolution=config.get("resolution", "auto"),
            fps=config.get("fps", "original"),
            quality=config.get("quality", "auto"),
            codec=config.get("codec", "h264"),
            audio_mode=config.get("audio_mode", "keep"),
            zoom_enabled=bool(config.get("zoom_enabled", False)),
            zoom_intensity=int(config.get("zoom_intensity", 10)),
            zoom_mode=config.get("zoom_mode", "fixed"),
            subtitles_enabled=has_clip_subs,
            subtitle_path=clip_sub_path,
            subtitle_font_size=sub_font_size,
            subtitle_position=sub_position,
        )

        # Closure captures correct clip index
        def make_clip_cb(c_idx: int, c_total: int):
            def cb(pct: float):
                progress_cb("clip", pct, c_idx, c_total)
            return cb

        clip_cb = make_clip_cb(clip_idx, total_clips)

        try:
            FFmpegService.process_clip(
                str(temp_dl),
                str(clip_out),
                start_sec,
                end_sec,
                opts,
                clip_cb,
            )
            clips_done += 1
            logger.debug(f"[{job_id}] Clip {clip_idx}/{total_clips} done (subtitles={has_clip_subs})")
        except Exception as e:
            logger.error(f"[{job_id}] Clip {clip_idx} failed: {e}")
            # Continue with remaining clips

    # ── 6. Cleanup temporary download & intermediate subtitle files
    _cleanup_temp_files(out_dir, temp_clip_subs)
    logger.info(f"[{job_id}] {video.get('title')}: done ({clips_done}/{total_clips} clips)")
    return clips_done


def _cleanup_temp_files(out_dir: Path, temp_clip_subs: list[Path] | None = None):
    """Removes temporary download video and any temporary subtitle files."""
    # Remove _download_temp.*
    for p in out_dir.glob("_download_temp*"):
        try:
            p.unlink()
        except Exception as e:
            logger.warning(f"Could not remove {p}: {e}")

    # Remove temporary sliced srt files
    if temp_clip_subs:
        for p in temp_clip_subs:
            try:
                if p.exists():
                    p.unlink()
            except Exception:
                pass
