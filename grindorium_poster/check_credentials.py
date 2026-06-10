"""
Credential checker. Run this BEFORE starting main.py. It makes read only
calls to every enabled platform and tells you which credentials work.
Nothing is posted.

Usage: python check_credentials.py
"""
import json
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent


def load_config():
    p = BASE / "config.json"
    if not p.exists():
        raise SystemExit("config.json not found. Copy config.example.json and fill it.")
    return json.loads(p.read_text(encoding="utf-8"))


def check_twitter(cfg):
    try:
        from requests_oauthlib import OAuth1
    except ImportError:
        return False, "requests-oauthlib not installed. pip install -r requirements.txt"
    auth = OAuth1(cfg["api_key"], cfg["api_secret"], cfg["access_token"], cfg["access_token_secret"])
    r = requests.get("https://api.twitter.com/2/users/me", auth=auth, timeout=30)
    if r.status_code == 200:
        return True, "@" + r.json()["data"]["username"]
    return False, f"HTTP {r.status_code}: {r.text[:200]}"


def check_facebook(cfg):
    r = requests.get(f"https://graph.facebook.com/v19.0/{cfg['page_id']}",
                     params={"fields": "name", "access_token": cfg["page_access_token"]}, timeout=30)
    if r.status_code == 200:
        return True, "Page: " + r.json().get("name", "")
    return False, f"HTTP {r.status_code}: {r.text[:200]}"


def check_instagram(cfg):
    r = requests.get(f"https://graph.facebook.com/v19.0/{cfg['ig_user_id']}",
                     params={"fields": "username", "access_token": cfg["access_token"]}, timeout=30)
    if r.status_code == 200:
        return True, "@" + r.json().get("username", "")
    return False, f"HTTP {r.status_code}: {r.text[:200]}"


def check_pinterest(cfg):
    r = requests.get("https://api.pinterest.com/v5/user_account",
                     headers={"Authorization": f"Bearer {cfg['access_token']}"}, timeout=30)
    if r.status_code == 200:
        return True, "@" + r.json().get("username", "")
    return False, f"HTTP {r.status_code}: {r.text[:200]}"


def check_tiktok(cfg):
    r = requests.get("https://open.tiktokapis.com/v2/user/info/?fields=display_name",
                     headers={"Authorization": f"Bearer {cfg['access_token']}"}, timeout=30)
    if r.status_code == 200:
        return True, r.json().get("data", {}).get("user", {}).get("display_name", "ok")
    return False, f"HTTP {r.status_code}: {r.text[:200]}"


CHECKS = {
    "twitter": check_twitter,
    "facebook": check_facebook,
    "instagram": check_instagram,
    "pinterest": check_pinterest,
    "tiktok": check_tiktok,
}


def main():
    config = load_config()
    print("Checking credentials. Nothing will be posted.\n")
    for name, fn in CHECKS.items():
        cfg = config["platforms"].get(name, {})
        if not cfg.get("enabled"):
            print(f"  {name:<10} SKIPPED (enabled: false)")
            continue
        placeholder = any(isinstance(v, str) and (v.startswith("YOUR_") or v.isupper() and "_" in v and len(v) > 8 and v == v.upper() and not any(c.isdigit() for c in v)) for v in cfg.values())
        try:
            ok, info = fn(cfg)
        except requests.RequestException as exc:
            ok, info = False, str(exc)
        status = "OK     " if ok else "FAILED "
        print(f"  {name:<10} {status} {info}")
    print("\nAll OK platforms are ready for main.py")


if __name__ == "__main__":
    main()
