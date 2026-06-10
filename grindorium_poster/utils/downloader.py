"""
Video downloader. Uses yt-dlp to download the video file and pull the
original title, description and tags from YouTube.
"""
import json
import subprocess
import sys
from pathlib import Path


def download_video(video_id, download_dir, logger, timeout=900):
    """Returns (video_path, meta) or (None, None) on failure."""
    out_dir = Path(download_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    url = f"https://www.youtube.com/watch?v={video_id}"
    out_template = str(out_dir / f"{video_id}.%(ext)s")
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "-f", "bv*[ext=mp4][height<=1080]+ba[ext=m4a]/b[ext=mp4]/b",
        "--merge-output-format", "mp4",
        "--write-info-json",
        "-o", out_template,
        url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        logger.error("Download timed out for %s", video_id)
        return None, None
    if result.returncode != 0:
        logger.error("yt-dlp failed for %s: %s", video_id, result.stderr[-800:])
        return None, None

    video_path = out_dir / f"{video_id}.mp4"
    info_path = out_dir / f"{video_id}.info.json"
    if not video_path.exists():
        candidates = list(out_dir.glob(f"{video_id}.*"))
        candidates = [c for c in candidates if c.suffix in (".mp4", ".mkv", ".webm")]
        if not candidates:
            logger.error("Downloaded file not found for %s", video_id)
            return None, None
        video_path = candidates[0]

    meta = {"id": video_id, "title": "", "description": "", "tags": [], "duration": 0}
    if info_path.exists():
        try:
            info = json.loads(info_path.read_text(encoding="utf-8"))
            meta["title"] = info.get("title", "")
            meta["description"] = info.get("description", "")
            meta["tags"] = info.get("tags", []) or []
            meta["duration"] = info.get("duration", 0) or 0
        except json.JSONDecodeError:
            logger.warning("Could not parse info json for %s", video_id)
    return str(video_path), meta
