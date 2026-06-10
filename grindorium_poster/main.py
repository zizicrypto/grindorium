"""
Grindorium poster. Watches the YouTube channel, downloads new videos,
generates platform captions with Claude (fallback formatter if Claude is
unavailable), queues them, and posts to Instagram, TikTok, Facebook and X.
Pinterest runs on its own image schedule from the local asset folders.

Run on MAIN: python main.py
Stop with Ctrl+C. State survives restarts through state.json.
"""
import json
import logging
import time
from datetime import datetime, date, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path

from utils import youtube_monitor, downloader, ai_rewriter
from platforms import instagram, tiktok, facebook, twitter, pinterest

BASE = Path(__file__).resolve().parent

PLATFORM_MODULES = {
    "instagram": instagram,
    "tiktok": tiktok,
    "facebook": facebook,
    "twitter": twitter,
}


def setup_logger():
    logger = logging.getLogger("grindorium_poster")
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fh = RotatingFileHandler(BASE / "logs" / "poster.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


def load_config():
    cfg_path = BASE / "config.json"
    if not cfg_path.exists():
        raise SystemExit("config.json not found. Copy config.example.json to config.json and fill the keys.")
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def process_new_videos(config, state, logger):
    fresh = youtube_monitor.check_new_videos(config, state, logger)
    for entry in fresh:
        vid = entry["id"]
        logger.info("New video detected: %s %s", vid, entry["title"])
        state.setdefault("seen_video_ids", []).append(vid)
        video_path, meta = downloader.download_video(vid, BASE / config["paths"]["download_dir"], logger)
        if not video_path:
            logger.error("Skipping %s, download failed", vid)
            continue
        captions = ai_rewriter.rewrite_for_platforms(meta, config, logger)
        publish_at = datetime.now() + timedelta(minutes=config["schedule"].get("post_delay_minutes", 30))
        state.setdefault("queue", []).append({
            "video_id": vid,
            "video_path": str(video_path),
            "captions": captions,
            "publish_at": publish_at.isoformat(timespec="seconds"),
            "done_platforms": [],
        })
        logger.info("Queued %s for %s", vid, publish_at)


def process_queue(config, state, logger):
    now = datetime.now()
    remaining = []
    for item in state.get("queue", []):
        if datetime.fromisoformat(item["publish_at"]) > now:
            remaining.append(item)
            continue
        for name, module in PLATFORM_MODULES.items():
            if name in item["done_platforms"]:
                continue
            pcfg = config["platforms"].get(name, {})
            if not pcfg.get("enabled"):
                item["done_platforms"].append(name)
                continue
            try:
                module.post(item["video_path"], item["captions"], config, logger)
                item["done_platforms"].append(name)
            except Exception as exc:
                logger.error("%s post failed for %s: %s", name, item["video_id"], exc)
        if set(item["done_platforms"]) >= set(PLATFORM_MODULES):
            logger.info("All platforms done for %s", item["video_id"])
        else:
            remaining.append(item)
    state["queue"] = remaining


def pinterest_scheduler(config, state, logger):
    """Fires quote pins at the configured local times and a result pin every N days."""
    if not config["platforms"].get("pinterest", {}).get("enabled"):
        return
    pst = state.setdefault("pinterest", {"quote_index": 0, "result_index": 0, "posted_log": []})
    today = date.today().isoformat()
    now_hm = datetime.now().strftime("%H:%M")

    fired = pst.setdefault("fired", {})
    if fired.get("day") != today:
        fired.clear()
        fired["day"] = today

    for slot in config["schedule"].get("pinterest_quote_times", []):
        key = f"quote_{slot}"
        if fired.get(key):
            continue
        if now_hm >= slot:
            try:
                if pinterest.post_next_quote(config, state, logger):
                    fired[key] = True
            except Exception as exc:
                logger.error("Pinterest quote pin failed: %s", exc)
                fired[key] = True

    every = config["schedule"].get("pinterest_result_every_days", 2)
    last = pst.get("last_result_day", "")
    due = (not last) or (date.fromisoformat(last) + timedelta(days=every) <= date.today())
    if due and now_hm >= config["schedule"].get("pinterest_result_time", "18:00") and not fired.get("result"):
        try:
            if pinterest.post_next_result(config, state, logger):
                pst["last_result_day"] = today
                fired["result"] = True
        except Exception as exc:
            logger.error("Pinterest result pin failed: %s", exc)
            fired["result"] = True


def main():
    logger = setup_logger()
    config = load_config()
    state_path = BASE / config["paths"]["state_file"]
    state = youtube_monitor.load_state(state_path)
    poll_seconds = max(60, int(config["youtube"].get("poll_interval_minutes", 10)) * 60)
    logger.info("Grindorium poster started. Poll every %s seconds.", poll_seconds)

    last_poll = 0.0
    while True:
        try:
            now = time.time()
            if now - last_poll >= poll_seconds:
                last_poll = now
                process_new_videos(config, state, logger)
            process_queue(config, state, logger)
            pinterest_scheduler(config, state, logger)
            youtube_monitor.save_state(state, state_path)
        except KeyboardInterrupt:
            logger.info("Stopping. State saved.")
            youtube_monitor.save_state(state, state_path)
            break
        except Exception as exc:
            logger.error("Loop error, continuing: %s", exc)
        time.sleep(30)


if __name__ == "__main__":
    main()
