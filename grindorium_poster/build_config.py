"""
GitHub Actions runner'inda calisir. GitHub repo secrets'lardan gecici bir
config.json olusturur (asla commit edilmez, .gitignore'da zaten var).
Local PC'deki config.json'un yerini TUTMAZ - o dosya PC'de kalmaya devam
eder, bu sadece bulut calistirmasi icin ayni sekli bulut ortaminda kurar.
"""
import base64
import json
import os

cookies_b64 = os.environ.get("YOUTUBE_COOKIES_B64", "")
if cookies_b64:
    with open("cookies.txt", "wb") as f:
        f.write(base64.b64decode(cookies_b64))
    print("cookies.txt olusturuldu.")

config = {
    "youtube": {
        "channel_id": os.environ["YOUTUBE_CHANNEL_ID"],
        "poll_interval_minutes": 15,
    },
    "claude": {"enabled": False, "api_key": "", "model": ""},
    "paths": {"download_dir": "downloads", "state_file": "state.json"},
    "schedule": {
        "stickline_start_date": None,
        "grindorium_start_date": None,
        "stickline_min_hours_between": 6,
        "grindorium_min_hours_between": 20,
    },
    "platforms": {
        "instagram": {
            "enabled": True,
            "access_token": os.environ["IG_ACCESS_TOKEN"],
            "ig_user_id": os.environ["IG_USER_ID"],
        },
        "facebook": {
            "enabled": True,
            "page_id": os.environ["FB_PAGE_ID"],
            "page_access_token": os.environ["FB_PAGE_ACCESS_TOKEN"],
        },
        "tiktok": {"enabled": False},
        "twitter": {"enabled": False},
        "pinterest": {"enabled": False},
    },
}

with open("config.json", "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2)
print("config.json olusturuldu.")
