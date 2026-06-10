"""
TikTok module. Uses the Content Posting API direct upload flow.
Important: until the app passes the TikTok audit, uploads land as drafts
that must be approved inside the TikTok app. The code logs this clearly.
"""
import os

import requests

INIT_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"


def post(video_path, captions, config, logger):
    cfg = config["platforms"]["tiktok"]
    token = cfg["access_token"]
    size = os.path.getsize(video_path)
    chunk_size = min(size, 64 * 1024 * 1024)

    init = requests.post(INIT_URL, timeout=60,
                         headers={"Authorization": f"Bearer {token}",
                                  "Content-Type": "application/json"},
                         json={
                             "post_info": {
                                 "title": captions["tiktok"]["caption"][:2200],
                                 "privacy_level": "SELF_ONLY",
                             },
                             "source_info": {
                                 "source": "FILE_UPLOAD",
                                 "video_size": size,
                                 "chunk_size": chunk_size,
                                 "total_chunk_count": max(1, (size + chunk_size - 1) // chunk_size),
                             },
                         })
    init.raise_for_status()
    data = init.json().get("data", {})
    upload_url = data.get("upload_url")
    if not upload_url:
        raise RuntimeError(f"TikTok init failed: {init.text[:300]}")

    sent = 0
    with open(video_path, "rb") as f:
        while sent < size:
            chunk = f.read(chunk_size)
            end = sent + len(chunk) - 1
            up = requests.put(upload_url, timeout=900, data=chunk, headers={
                "Content-Range": f"bytes {sent}-{end}/{size}",
                "Content-Type": "video/mp4",
            })
            up.raise_for_status()
            sent += len(chunk)

    logger.info("TikTok upload finished. If the app is not audited yet this video sits as a draft. Open the TikTok app to approve it.")
    return True
