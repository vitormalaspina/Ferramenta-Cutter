import re


def sanitize_filename(name: str) -> str:
    if not name:
        return "video"
    # Replace invalid filesystem characters with underscore
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Collapse multiple underscores/spaces into a single underscore
    name = re.sub(r'[\s_]+', '_', name)
    name = name.strip(' ._')
    return name[:100] or "video"
