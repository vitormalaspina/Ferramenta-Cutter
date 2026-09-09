def parse_duration(s: str) -> int:
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
