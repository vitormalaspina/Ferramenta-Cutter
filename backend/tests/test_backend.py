import sys
from pathlib import Path

# Ensure backend root is on sys.path for direct IDE execution or standalone pytest runs
BACKEND_DIR = Path(__file__).parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from utils.duration import parse_duration, format_duration, calculate_clips
from utils.sanitize import sanitize_filename
from services.disk_service import DiskService
from services.ffmpeg_service import FFmpegService, ProcessOptions
from services.job_service import JobService
from services.subtitle_service import SubtitleService
from models.database import Base, engine


def setup_module():
    Base.metadata.create_all(bind=engine)


def test_sanitize_filename():
    assert sanitize_filename("Video / Name : With * Bad ? Chars") == "Video_Name_With_Bad_Chars"
    assert sanitize_filename('test\\path/foo:bar*baz?"<pipe>|') == "test_path_foo_bar_baz_pipe"
    assert len(sanitize_filename("a" * 200)) <= 100


def test_parse_duration():
    assert parse_duration("01:30") == 90
    assert parse_duration("00:45") == 45
    assert parse_duration("01:12:42") == 4362
    assert parse_duration("60") == 60
    assert parse_duration("") == 0


def test_format_duration():
    assert format_duration(90) == "1:30"
    assert format_duration(45) == "0:45"
    assert format_duration(4362) == "1:12:42"
    assert format_duration(0) == "0:00"


def test_calculate_clips():
    # 8:37 = 517s, clip duration 90s (1:30)
    # 517 / 90 = 5 clips of 90s (0-450s) + 67s remaining (450-517s)
    clips_keep = calculate_clips(517, 90, keep_last=True)
    assert len(clips_keep) == 6
    assert clips_keep[0] == {"start": 0, "end": 90, "index": 1}
    assert clips_keep[1] == {"start": 90, "end": 180, "index": 2}
    assert clips_keep[4] == {"start": 360, "end": 450, "index": 5}
    assert clips_keep[5] == {"start": 450, "end": 517, "index": 6}

    clips_drop = calculate_clips(517, 90, keep_last=False)
    assert len(clips_drop) == 5
    assert clips_drop[-1]["end"] == 450


def test_disk_service():
    free_bytes = DiskService.get_available_space("/")
    assert free_bytes > 0
    ok, avail, req = DiskService.check_space("/", 1024)
    assert ok is True
    assert avail > req


def test_ffmpeg_filter_building():
    opts_916 = ProcessOptions(output_format='9:16', resolution='1080x1920')
    vf = FFmpegService.build_filter_complex(opts_916)
    assert "crop=1080:1920" in vf

    opts_11 = ProcessOptions(output_format='1:1')
    vf = FFmpegService.build_filter_complex(opts_11)
    assert "1080:1080" in vf

    opts_zoom = ProcessOptions(output_format='9:16', zoom_enabled=True, zoom_intensity=15)
    vf = FFmpegService.build_filter_complex(opts_zoom)
    assert "crop" in vf


def test_job_service_crud():
    job_data = {
        "source_id": "test-source-id",
        "source_type": "channel",
        "source_url": "https://youtube.com/@test",
        "channel_name": "Canal de Teste",
        "config": {"output_format": "9:16", "clip_duration_seconds": 90},
    }
    videos_data = [
        {"id": "vid1", "title": "Video 1", "url": "https://youtube.com/watch?v=vid1", "duration_seconds": 120},
        {"id": "vid2", "title": "Video 2", "url": "https://youtube.com/watch?v=vid2", "duration_seconds": 300},
    ]

    job = JobService.create_job(job_data, videos_data)
    assert job.id is not None
    assert job.channel_name == "Canal de Teste"

    detail = JobService.get_job_detail(job.id)
    assert detail is not None
    assert detail["total_videos"] == 2
    assert detail["status"] == "pending"

    JobService.update_job_status(job.id, "processing", progress={"progress_percent": 50})
    updated = JobService.get_job_detail(job.id)
    assert updated["status"] == "processing"
    assert updated["progress_percent"] == 50

    jobs = JobService.list_jobs()
    assert any(j["job_id"] == job.id for j in jobs)

    JobService.delete_job(job.id)
    assert JobService.get_job(job.id) is None


def test_subtitle_service(tmp_path):
    vtt_sample = """WEBVTT
Kind: captions
Language: pt

00:00:01.000 --> 00:00:03.500
<c>Olá,</c><c> bem-vindos</c> ao nosso vídeo!

00:00:04.200 --> 00:00:08.000
Hoje vamos mostrar a fábrica de bolachas.

00:00:10.000 --> 00:00:15.000
Esta parte fica de fora do corte.
"""
    vtt_file = tmp_path / "_download_temp.pt.vtt"
    vtt_file.write_text(vtt_sample, encoding="utf-8")

    cues = SubtitleService.find_and_parse_subtitles(tmp_path, "_download_temp")
    assert len(cues) == 3
    assert cues[0]["text"] == "Olá, bem-vindos ao nosso vídeo!"
    assert cues[0]["start"] == 1.0

    # Slice for clip from 2 to 9 seconds
    clip_srt = tmp_path / "corte_001.srt"
    has_subs = SubtitleService.slice_cues_to_srt(cues, 2.0, 9.0, clip_srt)
    assert has_subs is True
    assert clip_srt.exists()

    content = clip_srt.read_text(encoding="utf-8")
    assert "00:00:00,000 --> 00:00:01,500" in content
    assert "Olá, bem-vindos ao nosso vídeo!" in content
    assert "Hoje vamos mostrar a fábrica" in content
    assert "de bolachas." in content
    assert "Esta parte fica de fora do corte." not in content

    sub_filter = SubtitleService.build_ffmpeg_subtitles_filter(str(clip_srt))
    assert "subtitles=" in sub_filter
    assert "PrimaryColour=&H0000FFFF" in sub_filter
