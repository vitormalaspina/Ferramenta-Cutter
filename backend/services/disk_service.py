import shutil

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
