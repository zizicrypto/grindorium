"""
Updates videos.json with the latest long videos from the Grindorium YouTube channel.
Uses YouTube Data API v3 (public read-only, API key via YOUTUBE_API_KEY env var).
Filters out Shorts by duration. Writes newest first.
Usage: python tools/update_watch_videos.py
Then commit and push videos.json.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from googleapiclient.discovery import build

MIN_DURATION_SECONDS = 120
MAX_VIDEOS = 24
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT = REPO_ROOT / "videos.json"


def _parse_iso_duration(iso):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    h, mn, s = (int(x or 0) for x in m.groups())
    return h * 3600 + mn * 60 + s


def fetch_channel_videos():
    api_key = os.environ["YOUTUBE_API_KEY"]
    yt = build("youtube", "v3", developerKey=api_key)

    ch = yt.channels().list(part="contentDetails", forHandle="@Grindorium").execute()
    pid = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    items, seen, page = [], set(), None
    while len(items) < 40:
        r = yt.playlistItems().list(
            part="contentDetails,snippet", playlistId=pid,
            maxResults=50, pageToken=page
        ).execute()
        for item in r.get("items", []):
            vid = item["contentDetails"]["videoId"]
            if vid not in seen:
                seen.add(vid)
                items.append(item)
        page = r.get("nextPageToken")
        if not page:
            break
    items = items[:40]

    vid_ids = [item["contentDetails"]["videoId"] for item in items]
    details = {}
    for i in range(0, len(vid_ids), 50):
        resp = yt.videos().list(
            part="contentDetails", id=",".join(vid_ids[i:i + 50])
        ).execute()
        for v in resp.get("items", []):
            details[v["id"]] = v["contentDetails"]["duration"]

    results = []
    for item in items:
        vid = item["contentDetails"]["videoId"]
        if vid not in details:
            continue
        snip = item["snippet"]
        upload_date = snip.get("publishedAt", "")[:10].replace("-", "")
        results.append({
            "id": vid,
            "title": snip.get("title", ""),
            "upload_date": upload_date,
            "duration": _parse_iso_duration(details[vid]),
        })
    return results


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
