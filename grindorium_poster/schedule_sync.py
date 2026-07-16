"""
STICKLINE_RESCHEDULE_STATE.json'daki video_id -> publishAt(+kind) bilgisini
grindorium_poster/schedule.json'a kopyalar ve git'e commit+push eder. Bu,
cloud_poster.py'nin (GitHub Actions) hangi videonun ne zaman yayinlanacagini
onceden bilmesini saglar - PC her calistiginda (STICKLINE uretimi/reschedule
sonrasi) elle calistirilir, siir/gizli bilgi icermez (sadece video_id,
tarih, kisa tur etiketi).

Kullanim: python schedule_sync.py [--no-push]
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STICKLINE_STATE = Path(r"C:\Users\Ali\Desktop\STICKLINE\STICKLINE_RESCHEDULE_STATE.json")
BASE = Path(__file__).parent
SCHEDULE_OUT = BASE / "schedule.json"


def build_schedule():
    if not STICKLINE_STATE.exists():
        print(f"UYARI: {STICKLINE_STATE} bulunamadi, sync atlaniyor.")
        return None
    raw = json.loads(STICKLINE_STATE.read_text(encoding="utf-8"))
    videos = {}
    for vid, entry in raw.items():
        publish_at = entry.get("new_publishAt")
        kind = entry.get("kind")
        if not publish_at or not kind:
            continue  # elle mudahale edilmis / tur belirsiz kayitlar atlanir
        videos[vid] = {"publishAt": publish_at, "kind": kind}
    return {
        "synced_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": str(STICKLINE_STATE),
        "videos": videos,
    }


def main():
    no_push = "--no-push" in sys.argv
    schedule = build_schedule()
    if schedule is None:
        return 1

    SCHEDULE_OUT.write_text(json.dumps(schedule, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(schedule['videos'])} video schedule.json'a yazildi.")

    status = subprocess.run(
        ["git", "status", "--porcelain", "--", str(SCHEDULE_OUT)],
        cwd=BASE.parent, capture_output=True, text=True, check=True,
    )
    if not status.stdout.strip():
        print("Degisiklik yok, commit atlaniyor.")
        return 0

    subprocess.run(["git", "add", str(SCHEDULE_OUT)], cwd=BASE.parent, check=True)
    subprocess.run(
        ["git", "commit", "-m", "grindorium_poster: schedule.json senkronize edildi"],
        cwd=BASE.parent, check=True,
    )
    if no_push:
        print("Commit yapildi, --no-push nedeniyle push atlandi.")
        return 0
    subprocess.run(["git", "push"], cwd=BASE.parent, check=True)
    print("Push edildi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
