"""
Instagram Reels module. Uses the Graph API resumable upload flow:
create a media container with upload_type resumable, push the file bytes
to rupload, then publish the container. Needs an Instagram Business
account linked to a Facebook page and an approved Meta app.
"""
import os
import time

import requests

GRAPH = "https://graph.facebook.com/v19.0"
RUPLOAD = "https://rupload.facebook.com/ig-api-upload/v19.0"


def post(video_path, captions, config, logger):
    cfg = config["platforms"]["instagram"]
    token = cfg["access_token"]
    ig_user = cfg["ig_user_id"]

    container = requests.post(f"{GRAPH}/{ig_user}/media", timeout=60, data={
        "access_token": token,
        "media_type": "REELS",
        "upload_type": "resumable",
        "caption": captions["instagram"]["caption"],
    })
    if not container.ok:
        raise RuntimeError(f"Instagram container {container.status_code}: {container.text[:500]}")
    container_id = container.json()["id"]
    logger.info("Instagram container: %s", container_id)

    size = os.path.getsize(video_path)
    with open(video_path, "rb") as f:
        up = requests.post(f"{RUPLOAD}/{container_id}", timeout=900,
                           headers={"Authorization": f"OAuth {token}",
                                    "offset": "0",
                                    "file_size": str(size),
                                    "Content-Type": "application/octet-stream"},
                           data=f)
    if not up.ok:
        raise RuntimeError(f"Instagram upload {up.status_code}: {up.text[:500]}")

    for _ in range(40):
        status = requests.get(f"{GRAPH}/{container_id}", timeout=30,
                              params={"fields": "status_code,status", "access_token": token})
        if not status.ok:
            raise RuntimeError(f"Instagram status check {status.status_code}: {status.text[:500]}")
        status_data = status.json()
        code = status_data.get("status_code")
        if code == "FINISHED":
            break
        if code == "ERROR":
            raise RuntimeError(f"Instagram container processing failed: {status_data}")
        time.sleep(15)

    pub = requests.post(f"{GRAPH}/{ig_user}/media_publish", timeout=60,
                        data={"creation_id": container_id, "access_token": token})
    if not pub.ok:
        raise RuntimeError(f"Instagram publish {pub.status_code}: {pub.text[:500]}")
    logger.info("Instagram posted: %s", pub.json().get("id"))
    return True
