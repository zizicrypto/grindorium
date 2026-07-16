"""
Facebook video module. Kisa videolar Reels API (video_reels, 3 fazli:
start/upload/finish) ile, uzun (LONG) videolar normal Page video postu
(POST /{page_id}/videos, dogrudan multipart yukleme) ile paylasilir.
Facebook Reels'in sure siniri var (kisa format icin tasarlanmis); STICKLINE
LONG videolari o siniri asabildigi icin Reels yerine normal video postu
kullanilir - Reels akisiyla zorlanirsa 2026-07-10'daki gibi 400 hatasi
riski var (README grindorium_poster/README.md Bolum 10).

Scheduled publishing (sadece Reels akisinda) desteklenir: pass
scheduled_publish_time as a Unix timestamp (int) ve Reel SCHEDULED olarak
kuyruklanir. scheduled_publish_time verilmezse aninda PUBLISHED olur.
"""
import os

import requests

GRAPH = "https://graph.facebook.com/v19.0"


def post(video_path, captions, config, logger, scheduled_publish_time=None, kind="SHORT"):
    if kind == "LONG":
        return _post_long_video(video_path, captions, config, logger)
    return _post_reel(video_path, captions, config, logger, scheduled_publish_time)


def _post_long_video(video_path, captions, config, logger):
    """Normal Page video postu (Reels degil). Uzun formatlar icin."""
    cfg = config["platforms"]["facebook"]
    token = cfg["page_access_token"]
    page_id = cfg["page_id"]
    caption = captions["facebook"]["caption"]

    with open(video_path, "rb") as f:
        resp = requests.post(
            f"{GRAPH}/{page_id}/videos",
            timeout=900,
            data={"description": caption, "access_token": token},
            files={"source": f},
        )
    if not resp.ok:
        raise RuntimeError(f"Facebook video postu {resp.status_code}: {resp.text[:300]}")
    result = resp.json()
    video_id = result.get("id")
    if not video_id:
        raise RuntimeError(f"Facebook video postu: id eksik: {resp.text[:300]}")
    logger.info("Facebook (LONG) video postu yayinlandi: video_id=%s", video_id)
    return True


def _post_reel(video_path, captions, config, logger, scheduled_publish_time):
    cfg = config["platforms"]["facebook"]
    token = cfg["page_access_token"]
    page_id = cfg["page_id"]
    caption = captions["facebook"]["caption"]

    # Faz 1: Upload session baslat, video_id + upload_url al
    start = requests.post(
        f"{GRAPH}/{page_id}/video_reels",
        timeout=60,
        data={"upload_phase": "start", "access_token": token},
    )
    if not start.ok:
        raise RuntimeError(f"Facebook Reels start {start.status_code}: {start.text[:300]}")
    start_data = start.json()
    video_id = start_data.get("video_id")
    upload_url = start_data.get("upload_url")
    if not video_id or not upload_url:
        raise RuntimeError(f"Facebook Reels start: video_id veya upload_url eksik: {start.text[:200]}")
    logger.info("Facebook Reels session: video_id=%s", video_id)

    # Faz 2: Video binary yukle (rupload.facebook.com)
    size = os.path.getsize(video_path)
    with open(video_path, "rb") as f:
        up = requests.post(
            upload_url,
            timeout=900,
            headers={
                "Authorization": f"OAuth {token}",
                "offset": "0",
                "file_size": str(size),
            },
            data=f,
        )
    if not up.ok:
        raise RuntimeError(f"Facebook Reels upload {up.status_code}: {up.text[:300]}")
    logger.info("Facebook Reels yuklendi: %d bytes", size)

    # Faz 3: Yayinla (PUBLISHED veya SCHEDULED)
    state = "SCHEDULED" if scheduled_publish_time else "PUBLISHED"
    finish_data = {
        "video_id": video_id,
        "upload_phase": "finish",
        "video_state": state,
        "description": caption,
        "access_token": token,
    }
    if scheduled_publish_time:
        finish_data["scheduled_publish_time"] = str(int(scheduled_publish_time))

    finish = requests.post(
        f"{GRAPH}/{page_id}/video_reels",
        timeout=60,
        data=finish_data,
    )
    if not finish.ok:
        raise RuntimeError(f"Facebook Reels finish {finish.status_code}: {finish.text[:300]}")
    result = finish.json()
    if not result.get("success"):
        raise RuntimeError(f"Facebook Reels finish success=False: {finish.text[:300]}")

    logger.info("Facebook Reels yayinlandi: video_id=%s state=%s", video_id, state)
    return True
