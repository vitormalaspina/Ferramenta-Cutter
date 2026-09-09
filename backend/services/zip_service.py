import shutil
from pathlib import Path
import os
from utils.logger import get_logger

logger = get_logger(__name__)


class ZipService:
    @staticmethod
    def create_zip(job_id: str, clips_dir: str, output_path: str) -> str:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        base_name = str(out).removesuffix('.zip')
        logger.info(f"Creating ZIP archive for job {job_id} at {out} from {clips_dir}")
        shutil.make_archive(base_name, 'zip', root_dir=clips_dir)
        return str(out)

    @staticmethod
    def estimate_size(directory: str) -> int:
        total = 0
        if not os.path.exists(directory):
            return 0
        for dirpath, _, filenames in os.walk(directory):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    try:
                        total += os.path.getsize(fp)
                    except OSError:
                        pass
        return total
