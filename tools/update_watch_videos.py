"""
Updates videos.json with the latest long videos from the Grindorium YouTube channel.
Run on MAIN. Requires yt-dlp installed (pip install yt-dlp).
Filters out Shorts by duration. Writes newest first.
Usage: python tools/update_watch_videos.py
Then commit and push videos.json.
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CHANNEL_URL = "https://www.youtube.com/@Grindorium/videos"
MIN_DURATION_SECONDS = 120
MAX_VIDEOS = 24
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT = REPO_ROOT / "videos.json"


def fetch_channel_videos():
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--skip-download",
        "--dump-json",
        "--playlist-end", "40",
        CHANNEL_URL,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        print("yt-dlp failed:")
        print(result.stderr[-2000:])
        sys.exit(1)
    videos = []
    for line in result.stdout.strip().splitlines():
        try:
            videos.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return videos


def main():
    raw = fetch_channel_videos()
    longs = []
    for v in raw:
        duration = v.get("duration") or 0
        if duration < MIN_DURATION_SECONDS:
            continue
        upload_date = v.get("upload_date") or ""
        published = ""
        if len(upload_date) == 8:
            published = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
        longs.append({
            "id": v.get("id", ""),
            "title": v.get("title", ""),
            "published": published,
            "duration": duration,
        })
        if len(longs) >= MAX_VIDEOS:
            break

    data = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "note": "Updated by tools/update_watch_videos.py. Long videos only, newest first.",
        "videos": longs,
    }
    OUTPUT.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(longs)} long videos to {OUTPUT}")
    for v in longs:
        print(f"  {v['id']}  {v['duration']:>5}s  {v['title'][:60]}")


if __name__ == "__main__":
    main()
