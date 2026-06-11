"""
Facebook Page module. Publishes the video to the page through the Graph API
video upload endpoint. Needs a page access token with the video publish
permission, which requires app review.
"""
import requests

GRAPH = "https://graph-video.facebook.com/v19.0"


def post(video_path, captions, config, logger):
    cfg = config["platforms"]["facebook"]
    url = f"{GRAPH}/{cfg['page_id']}/videos"
    caption = captions["facebook"]["caption"]
    title = caption.split("\n")[0][:100]
    with open(video_path, "rb") as f:
        resp = requests.post(url, timeout=900,
                             data={"access_token": cfg["page_access_token"],
                                   "title": title, "description": caption},
                             files={"source": f})
    if not resp.ok:
        raise RuntimeError(f"Facebook {resp.status_code}: {resp.text[:300]}")
    logger.info("Facebook posted: %s", resp.json().get("id"))
    return True
