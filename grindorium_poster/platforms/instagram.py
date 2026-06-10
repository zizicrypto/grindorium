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
    container.raise_for_status()
    container_id = container.json()["id"]

    size = os.path.getsize(video_path)
    with open(video_path, "rb") as f:
        up = requests.post(f"{RUPLOAD}/{container_id}", timeout=900,
                           headers={"Authorization": f"OAuth {token}",
                                    "offset": "0",
                                    "file_size": str(size)},
                           data=f)
    up.raise_for_status()

    for _ in range(40):
        status = requests.get(f"{GRAPH}/{container_id}", timeout=30,
                              params={"fields": "status_code", "access_token": token})
        status.raise_for_status()
        code = status.json().get("status_code")
        if code == "FINISHED":
            break
        if code == "ERROR":
            raise RuntimeError("Instagram container processing failed")
        time.sleep(15)

    pub = requests.post(f"{GRAPH}/{ig_user}/media_publish", timeout=60,
                        data={"creation_id": container_id, "access_token": token})
    pub.raise_for_status()
    logger.info("Instagram posted: %s", pub.json().get("id"))
    return True
