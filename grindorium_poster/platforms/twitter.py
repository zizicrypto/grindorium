"""
X (Twitter) module. Uploads the video with the v1.1 chunked media endpoint
and posts the tweet with the v2 endpoint. Free tier allows about 500 writes
per month which covers one Short per day easily.
"""
import os
import time

import requests
from requests_oauthlib import OAuth1

MEDIA_URL = "https://upload.twitter.com/1.1/media/upload.json"
TWEET_URL = "https://api.twitter.com/2/tweets"


def _auth(cfg):
    return OAuth1(cfg["api_key"], cfg["api_secret"], cfg["access_token"], cfg["access_token_secret"])


def post(video_path, captions, config, logger):
    cfg = config["platforms"]["twitter"]
    auth = _auth(cfg)
    size = os.path.getsize(video_path)

    init = requests.post(MEDIA_URL, auth=auth, data={
        "command": "INIT", "media_type": "video/mp4",
        "total_bytes": size, "media_category": "tweet_video"}, timeout=60)
    init.raise_for_status()
    media_id = init.json()["media_id_string"]

    seg = 0
    with open(video_path, "rb") as f:
        while True:
            chunk = f.read(4 * 1024 * 1024)
            if not chunk:
                break
            up = requests.post(MEDIA_URL, auth=auth,
                               data={"command": "APPEND", "media_id": media_id, "segment_index": seg},
                               files={"media": chunk}, timeout=300)
            up.raise_for_status()
            seg += 1

    fin = requests.post(MEDIA_URL, auth=auth, data={"command": "FINALIZE", "media_id": media_id}, timeout=60)
    fin.raise_for_status()
    info = fin.json().get("processing_info", {})
    while info.get("state") in ("pending", "in_progress"):
        time.sleep(info.get("check_after_secs", 5))
        st = requests.get(MEDIA_URL, auth=auth, params={"command": "STATUS", "media_id": media_id}, timeout=60)
        st.raise_for_status()
        info = st.json().get("processing_info", {})
    if info.get("state") == "failed":
        raise RuntimeError(f"X media processing failed: {info}")

    tweet = requests.post(TWEET_URL, auth=auth, json={
        "text": captions["twitter"]["caption"],
        "media": {"media_ids": [media_id]}}, timeout=60)
    tweet.raise_for_status()
    logger.info("X posted: %s", tweet.json().get("data", {}).get("id"))
    return True
