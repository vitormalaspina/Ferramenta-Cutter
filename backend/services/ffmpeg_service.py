import subprocess
import json
import re
from pathlib import Path
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
    subtitles_enabled: bool = False
    subtitle_path: str | None = None
    subtitle_font_size: int = 28
    subtitle_position: str = 'bottom'


class FFmpegService:
    @staticmethod
    def get_video_info(path: str) -> dict:
        cmd = [
            'ffprobe', '-v', 'error',
            '-print_format', 'json',
            '-show_format', '-show_streams',
            path
        ]
        try:
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            data = json.loads(out)
            video_stream = next((s for s in data.get('streams', []) if s.get('codec_type') == 'video'), None)
            if not video_stream:
                return {}

            r_frame = video_stream.get('r_frame_rate', '30/1')
            fps = 30.0
            try:
                if '/' in r_frame:
                    num, den = r_frame.split('/', 1)
                    fps = float(num) / float(den) if float(den) != 0 else 30.0
                else:
                    fps = float(r_frame)
            except Exception:
                fps = 30.0

            return {
                'duration': float(data.get('format', {}).get('duration', 0)),
                'width': int(video_stream.get('width', 0)),
                'height': int(video_stream.get('height', 0)),
                'fps': fps
            }
        except Exception as e:
            logger.error(f"ffprobe error: {e}")
            return {}

    @staticmethod
    def build_filter_complex(options: ProcessOptions) -> str:
        filters = []

        # Resolution targets
        if options.output_format == '9:16':
            target_w = 720 if options.resolution == '720x1280' else 1080
            target_h = 1280 if options.resolution == '720x1280' else 1920
            # Scale to cover then center crop without deformation
            filters.append(
                f"scale='if(gt(a,{target_w}/{target_h}),-2,{target_w})':'if(gt(a,{target_w}/{target_h}),{target_h},-2)'"
            )
            filters.append(f"crop={target_w}:{target_h}")
        elif options.output_format == '1:1':
            target_dim = 1080
            filters.append(f"crop='min(iw,ih)':'min(iw,ih)',scale={target_dim}:{target_dim}")
        elif options.output_format == '16:9':
            target_w, target_h = 1920, 1080
            filters.append(
                f"scale='if(gt(a,{target_w}/{target_h}),-2,{target_w})':'if(gt(a,{target_w}/{target_h}),{target_h},-2)'"
            )
            filters.append(f"crop={target_w}:{target_h}")

        # Zoom filter
        if options.zoom_enabled and options.zoom_intensity > 0:
            zoom_factor = 1.0 + min(max(options.zoom_intensity, 1), 100) / 100.0
            # Center crop with zoom
            filters.append(
                f"crop='iw/{zoom_factor:.3f}':'ih/{zoom_factor:.3f}':(iw-iw/{zoom_factor:.3f})/2:(ih-ih/{zoom_factor:.3f})/2"
            )
            if options.output_format == '9:16':
                filters.append(f"scale={target_w}:{target_h}")
            elif options.output_format == '1:1':
                filters.append(f"scale={target_dim}:{target_dim}")
            elif options.output_format == '16:9':
                filters.append(f"scale={target_w}:{target_h}")

        # FPS filter
        if options.fps in ('30', '60'):
            filters.append(f"fps={options.fps}")

        # Subtitles burning filter (applied last so captions overlay on final resolution)
        if options.subtitles_enabled and options.subtitle_path and Path(options.subtitle_path).exists():
            from services.subtitle_service import SubtitleService
            sub_filter = SubtitleService.build_ffmpeg_subtitles_filter(
                options.subtitle_path,
                format=options.output_format,
                font_size=options.subtitle_font_size,
                position=options.subtitle_position
            )
            filters.append(sub_filter)

        return ",".join(filters) if filters else ""

    @staticmethod
    def process_clip(input_path: str, output_path: str, start_sec: int, end_sec: int, options: ProcessOptions, progress_callback):
        duration = max(1, end_sec - start_sec)
        cmd = [
            'ffmpeg', '-y',
            '-ss', str(start_sec),
            '-i', input_path,
            '-t', str(duration)
        ]

        vf = FFmpegService.build_filter_complex(options)
        if vf:
            cmd.extend(['-vf', vf])

        if options.audio_mode == 'remove':
            cmd.append('-an')
        else:
            cmd.extend(['-c:a', 'aac', '-b:a', '128k'])

        # Quality setting (CRF)
        crf = '23'
        if options.quality == 'high':
            crf = '19'
        elif options.quality == 'medium':
            crf = '24'
        elif options.quality == 'low':
            crf = '28'

        codec = 'libx264' if options.codec in ('h264', 'auto') else options.codec
        cmd.extend([
            '-c:v', codec,
            '-threads', '0',
            '-preset', 'superfast',
            '-crf', crf,
            '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart',
            output_path
        ])

        process = subprocess.Popen(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            universal_newlines=True,
            bufsize=1
        )
        time_regex = re.compile(r"time=\s*(\d+):(\d+):(\d+\.?\d*)")
        stderr_output = []

        if process.stderr:
            for line in process.stderr:
                stderr_output.append(line)
                match = time_regex.search(line)
                if match:
                    h, m, s = match.groups()
                    current_time = int(h) * 3600 + int(m) * 60 + float(s)
                    percent = min(99, int((current_time / duration) * 100))
                    if progress_callback:
                        progress_callback(percent)

        process.wait()
        if process.returncode != 0:
            err_snippet = "".join(stderr_output[-10:])
            logger.error(f"FFmpeg failed with code {process.returncode}: {err_snippet}")
            raise RuntimeError(f"FFmpeg falhou ao processar corte (código {process.returncode})")
        elif progress_callback:
            progress_callback(100)

    @staticmethod
    def cut_clip(input_path: str, output_path: str, start_sec: int, end_sec: int, options: ProcessOptions):
        FFmpegService.process_clip(input_path, output_path, start_sec, end_sec, options, None)
