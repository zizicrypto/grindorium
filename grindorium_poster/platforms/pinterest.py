"""
Pinterest module. Independent from the YouTube pipeline. Posts pre generated
quote and test result images from the local asset folders on its own
schedule. Tracks what was posted so nothing repeats until the pool is done.
"""
import base64
from pathlib import Path

import requests

PINS_URL = "https://api.pinterest.com/v5/pins"

QUOTE_DESCRIPTION = ("A daily reflection from Grindorium. Free psychology tools, "
                     "self assessments and quiet essays at grindorium.org")
RESULT_DESC_TEMPLATE = ("One of nine results from the free {test} on Grindorium. "
                        "Which one are you? Take the test at grindorium.org/{slug}")


def _post_image(image_path, title, description, link, config, logger):
    cfg = config["platforms"]["pinterest"]
    data = base64.b64encode(Path(image_path).read_bytes()).decode()
    resp = requests.post(PINS_URL, timeout=120,
                         headers={"Authorization": f"Bearer {cfg['access_token']}",
                                  "Content-Type": "application/json"},
                         json={
                             "board_id": cfg["board_id"],
                             "title": title[:100],
                             "description": description[:500],
                             "link": link,
                             "media_source": {
                                 "source_type": "image_base64",
                                 "content_type": "image/png",
                                 "data": data,
                             },
                         })
    resp.raise_for_status()
    logger.info("Pinterest pin created: %s (%s)", resp.json().get("id"), Path(image_path).name)
    return True


def post_next_quote(config, state, logger):
    quotes_dir = Path(config["paths"]["pinterest_quotes_dir"])
    files = sorted(quotes_dir.glob("*.png"))
    if not files:
        logger.warning("No quote images found in %s", quotes_dir)
        return False
    idx = state["pinterest"].get("quote_index", 0) % len(files)
    img = files[idx]
    ok = _post_image(img, "Grindorium Daily Quote", QUOTE_DESCRIPTION,
                     "https://grindorium.org/", config, logger)
    if ok:
        state["pinterest"]["quote_index"] = idx + 1
        state["pinterest"]["posted_log"].append(img.name)
    return ok


def post_next_result(config, state, logger):
    results_dir = Path(config["paths"]["pinterest_results_dir"])
    files = sorted(results_dir.glob("*.png"))
    if not files:
        logger.warning("No result images found in %s", results_dir)
        return False
    idx = state["pinterest"].get("result_index", 0) % len(files)
    img = files[idx]
    slug = img.name.split("_")[0]
    test_name = slug.replace("-", " ").title() + " Test"
    title = img.stem.split("_", 1)[-1].replace("-", " ").title()
    desc = RESULT_DESC_TEMPLATE.format(test=test_name, slug=slug)
    ok = _post_image(img, title, desc, f"https://grindorium.org/{slug}", config, logger)
    if ok:
        state["pinterest"]["result_index"] = idx + 1
        state["pinterest"]["posted_log"].append(img.name)
    return ok


def post_video(video_path, captions, config, logger):
    """Optional. Weekly long videos can also become pins later. Not used by default."""
    logger.info("Pinterest video pin skipped by design. Pinterest runs on the image schedule.")
    return True
