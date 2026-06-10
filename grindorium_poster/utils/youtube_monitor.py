"""
YouTube channel monitor. Polls the channel RSS feed and reports new videos.
No API key needed for detection. Seen video ids are stored in the state file.
"""
import json
import re
from pathlib import Path

import requests

RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={cid}"


def load_state(state_path):
    p = Path(state_path)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"seen_video_ids": [], "queue": [], "pinterest": {"quote_index": 0, "result_index": 0, "posted_log": []}}


def save_state(state, state_path):
    Path(state_path).write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def fetch_feed(channel_id, logger):
    url = RSS_URL.format(cid=channel_id)
    try:
        resp = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as exc:
        logger.warning("RSS fetch failed: %s", exc)
        return None


def parse_entries(xml_text):
    """Minimal RSS parse without external deps. Returns newest first."""
    entries = []
    for block in re.findall(r"<entry>(.*?)</entry>", xml_text, re.S):
        vid = re.search(r"<yt:videoId>([^<]+)</yt:videoId>", block)
        title = re.search(r"<title>([^<]*)</title>", block)
        published = re.search(r"<published>([^<]+)</published>", block)
        if vid:
            entries.append({
                "id": vid.group(1),
                "title": (title.group(1) if title else "").strip(),
                "published": published.group(1) if published else "",
            })
    return entries


def check_new_videos(config, state, logger):
    """Returns a list of entries not seen before, oldest first so they queue in order."""
    xml_text = fetch_feed(config["youtube"]["channel_id"], logger)
    if not xml_text:
        return []
    entries = parse_entries(xml_text)
    seen = set(state.get("seen_video_ids", []))
    fresh = [e for e in entries if e["id"] not in seen]
    fresh.reverse()
    return fresh
