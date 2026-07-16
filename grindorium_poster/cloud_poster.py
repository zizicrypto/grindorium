"""
Bulut (GitHub Actions) icin video-plan bazli paylasici. PC'ye bagimli
degildir - GitHub Actions runner'inda calisir.

Onceki sistemden (main.py + poster_check.py) farki: yeni video "tahmin"
edilmez. STICKLINE tarafi zaten her videoyu YouTube'a private+publishAt
ile (ileri tarihli, aylar onceden) yukluyor - schedule.json bu bilgiyi
(video_id -> publishAt + kind) tasiyor (bkz. schedule_sync.py). Bu script
sadece:
  1. schedule.json'daki, zamani gelmis (publishAt <= simdi) ve YouTube'da
     artik gercekten public olmus (RSS'te goruluyor) videolari bulur
     (content_type=stickline, kind biliniyor).
  2. schedule.json'da OLMAYAN ama RSS'te yeni beliren videolari da yakalar
     (content_type=grindorium - STICKLINE disi, orn. gercek bolum).
  3. Sirali (en eski once), rate-limit gate'i (schedule.min_hours_between)
     gecen ILK adayi indirir, Instagram+Facebook'a paylasir, tek durum
     dosyasina (posting_plan.json) isaretler.

Tek surec + tek durum dosyasi = eskiden yasanan cift-paylasim yarisi
(main.py/poster_check.py) yapisal olarak imkansiz hale gelir.

Flags:
  --dry-run   Log what would be done, make no real posts.
"""
import json
import logging
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent
SCHEDULE_FILE = BASE / "schedule.json"
POSTING_PLAN_FILE = BASE / "posting_plan.json"


def _setup_logger():
    logger = logging.getLogger("cloud_poster")
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    return logger


def _load_json(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default


def _parse_iso(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _validate_config(config, logger):
    """build_config.py bir secret'i bos/eksik birakmissa (orn. yanlis
    GitHub secret adi) bunu video indirmeden/harcamadan ONCE yakala -
    yarim/bozuk bir calistirma yerine net bir hatayla erken cik."""
    problems = []
    if not config.get("youtube", {}).get("channel_id"):
        problems.append("youtube.channel_id bos")
    for name in ("instagram", "facebook"):
        pcfg = config.get("platforms", {}).get(name, {})
        if not pcfg.get("enabled"):
            continue
        for field in (["access_token", "ig_user_id"] if name == "instagram"
                       else ["page_id", "page_access_token"]):
            if not pcfg.get(field):
                problems.append(f"platforms.{name}.{field} bos")
    if problems:
        for p in problems:
            logger.error("CONFIG HATASI: %s", p)
        return False
    return True


def _write_json_atomic(path, data, logger):
    """Yaziyi tamamlarken kesinti olursa (runner crash vb.) yarim/bozuk
    JSON diskte kalmasin diye: gecici dosyaya yaz, JSON olarak dogrula,
    sonra atomik rename ile gercek dosyanin yerine koy."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    text = json.dumps(data, indent=2, ensure_ascii=False)
    tmp.write_text(text, encoding="utf-8")
    try:
        json.loads(tmp.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        tmp.unlink(missing_ok=True)
        logger.error("DOGRULAMA HATASI: %s icin yazilan JSON bozuk, iptal: %s", path.name, exc)
        raise
    os.replace(tmp, path)


def _gating_ok(config, content_type):
    start = config["schedule"].get(content_type + "_start_date")
    if start and date.today() < date.fromisoformat(start):
        return False, start
    return True, None


def _rate_gate_ok(config, content_type, posting_plan):
    # 2026-07-16'da kanitlandi: bu kural "stickline" icin ARTIK YANLIS.
    # Eski (main.py/poster_check.py) sistemde video zamanlari tahmin
    # edildigi icin bir "backlog" birikip ayni anda birden fazla video
    # patlak verme riski vardi, bu kural onu onluyordu. Yeni sistemde
    # schedule.json + publishAt zaten dogru zamanlamayi garanti ediyor -
    # STICKLINE'in kendi programinda LONG+ESLI_SHORT ayni gun sadece 3 saat
    # arayla yayinlaniyor (bkz STICKLINE_SYSTEM.md), bu da 6 saatlik
    # "stickline_min_hours_between" kuralini HER ZAMAN tetikleyip ikinci
    # videoyu sonsuza kadar engelliyordu (RuCh8006niI/49MERGpa3Vs testinde
    # yakalandi). "stickline" (schedule.json kaynakli) icin kapatildi;
    # "grindorium" (RSS yedek yakalama, zamanlamasi garanti degil) icin
    # hala uygulaniyor.
    if content_type == "stickline":
        return True
    key = content_type + "_min_hours_between"
    min_hours = config["schedule"].get(key)
    if not min_hours:
        return True
    last = posting_plan.get("last_posted", {}).get(content_type)
    if not last:
        return True
    elapsed_h = (datetime.now(timezone.utc) - _parse_iso(last)).total_seconds() / 3600
    return elapsed_h >= min_hours


def _build_candidates(config, logger):
    from utils import youtube_monitor

    schedule = _load_json(SCHEDULE_FILE, {"videos": {}})
    posting_plan = _load_json(POSTING_PLAN_FILE, {"posted": {}, "last_posted": {}})
    posted_ids = set(posting_plan.get("posted", {}).keys())

    xml = youtube_monitor.fetch_feed(config["youtube"]["channel_id"], logger)
    rss_entries = youtube_monitor.parse_entries(xml) if xml else []
    rss_by_id = {e["id"]: e for e in rss_entries if e.get("id")}

    now = datetime.now(timezone.utc)
    candidates = []

    for vid, info in schedule.get("videos", {}).items():
        if vid in posted_ids:
            continue
        try:
            publish_dt = _parse_iso(info["publishAt"])
        except Exception:
            continue
        if now < publish_dt:
            continue
        if vid not in rss_by_id:
            # Planlanan saat gecmis ama YouTube'da henuz public gorunmuyor
            # (gecikme olabilir) - bir sonraki calistirmada tekrar denenir.
            continue
        entry = rss_by_id[vid]
        candidates.append({
            "id": vid,
            "title": entry.get("title", ""),
            "published": entry.get("published", info["publishAt"]),
            "content_type": "stickline",
            "kind": info.get("kind", "SHORT"),
        })

    for vid, entry in rss_by_id.items():
        if vid in posted_ids or vid in schedule.get("videos", {}):
            continue
        candidates.append({
            "id": vid,
            "title": entry.get("title", ""),
            "published": entry.get("published", ""),
            "content_type": "grindorium",
            "kind": "SHORT",
        })

    candidates.sort(key=lambda c: c["published"] or "")
    return candidates, posting_plan


def _post_video(entry, config, logger, dry_run):
    from utils import downloader, ai_rewriter
    from platforms import instagram, facebook, tiktok, twitter

    vid = entry["id"]
    content_type = entry["content_type"]
    fb_kind = "LONG" if entry["kind"] == "LONG" else "SHORT"

    platform_modules = {
        "instagram": instagram,
        "tiktok": tiktok,
        "facebook": facebook,
        "twitter": twitter,
    }
    if dry_run:
        enabled = [n for n in platform_modules if config["platforms"].get(n, {}).get("enabled")]
        logger.info("DRY-RUN: %s (%s/%s) icin %s platformuna gonderilecek",
                     vid, content_type, entry["kind"], enabled)
        return enabled

    video_path, meta = downloader.download_video(vid, BASE / config["paths"]["download_dir"], logger)
    if not video_path:
        logger.error("Download basarisiz: %s", vid)
        return []

    captions = ai_rewriter.rewrite_for_platforms(meta, config, logger, content_type=content_type)
    done = []
    for name, module in platform_modules.items():
        pcfg = config["platforms"].get(name, {})
        if not pcfg.get("enabled"):
            continue
        try:
            if name == "facebook":
                module.post(video_path, captions, config, logger, kind=fb_kind)
            else:
                module.post(video_path, captions, config, logger)
            done.append(name)
            logger.info("%s: basarili", name)
        except Exception as exc:
            logger.error("%s: hata: %s", name, exc)
    return done


def _mark_posted(posting_plan, entry, done_platforms, logger):
    posting_plan.setdefault("posted", {})[entry["id"]] = {
        "content_type": entry["content_type"],
        "kind": entry["kind"],
        "done_platforms": done_platforms,
        "posted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    posting_plan.setdefault("last_posted", {})[entry["content_type"]] = \
        datetime.now(timezone.utc).isoformat(timespec="seconds")
    _write_json_atomic(POSTING_PLAN_FILE, posting_plan, logger)


def main():
    dry_run = "--dry-run" in sys.argv
    logger = _setup_logger()
    tag = "[DRY-RUN] " if dry_run else ""

    config = json.loads((BASE / "config.json").read_text(encoding="utf-8"))
    if not _validate_config(config, logger):
        logger.error("Config gecersiz, cikiliyor (hicbir sey indirilmedi/paylasilmadi).")
        sys.exit(1)

    candidates, posting_plan = _build_candidates(config, logger)

    if not candidates:
        logger.info("%sZamani gelmis/yeni video yok. Cikiliyor.", tag)
        return

    for entry in candidates:
        content_type = entry["content_type"]
        ok, start_date = _gating_ok(config, content_type)
        if not ok:
            logger.info("%s%s: gating (%s henuz aktif degil, %s). Atlaniyor.",
                         tag, entry["id"], content_type, start_date)
            continue
        if not _rate_gate_ok(config, content_type, posting_plan):
            logger.info("%s%s: rate-limit gate acik degil (%s bekleme suresi dolmadi). Atlaniyor.",
                         tag, entry["id"], content_type)
            continue

        logger.info("%sPaylasilacak: %s | %s | tur=%s kind=%s",
                     tag, entry["id"], entry["title"], content_type, entry["kind"])
        done = _post_video(entry, config, logger, dry_run)

        if not dry_run:
            if done:
                _mark_posted(posting_plan, entry, done, logger)
                logger.info("Paylasim tamam: %s -> %s", entry["id"], done)
            else:
                logger.error("Hicbir platforma paylasilamadi: %s (bir sonraki calistirmada tekrar denenir)", entry["id"])
        else:
            logger.info("DRY-RUN tamamlandi. Gercek paylasim yapilmadi.")
        break  # her calistirmada tek video - sirali, guvenli


if __name__ == "__main__":
    main()
