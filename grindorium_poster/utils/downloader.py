"""
Video downloader. Uses yt-dlp to download the video file and pull the
original title, description and tags from YouTube.
"""
import json
import subprocess
import sys
from pathlib import Path

COOKIES_FILE = Path(__file__).resolve().parent.parent / "cookies.txt"


def download_video(video_id, download_dir, logger, timeout=900):
    """Returns (video_path, meta) or (None, None) on failure."""
    out_dir = Path(download_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    url = f"https://www.youtube.com/watch?v={video_id}"
    out_template = str(out_dir / f"{video_id}.%(ext)s")
    # -S "res:1080,vcodec:h264" ile secim yapiliyor (sabit "height<=1080"
    # filtresi DEGIL): STICKLINE short'lari dikey (1080x1920, yani height=1920)
    # oldugu icin eski "height<=1080" filtresi bunlari yanlislikla 480p'ye
    # dusuruyordu (genislik/yukseklik karisikligi, 2026-07-16'da kanitlandi).
    # -S siralama ipucu hem dikey hem yatay videoda doru calisir.
    base_cmd = [
        sys.executable, "-m", "yt_dlp",
        "-S", "res:1080,vcodec:h264",
        "-f", "bv*+ba/b",
        "--merge-output-format", "mp4",
        "--write-info-json",
        "-o", out_template,
    ]
    # GitHub Actions'in (ve genelde datacenter IP'lerinin) YouTube tarafindan
    # "bot" sanilip "Sign in to confirm you're not a bot" hatasiyla
    # engellenmesi bilinen bir sorun (2026-07-16'da cloud_poster'in ilk
    # gercek calistirmasinda kanitlandi; android client tek basina da
    # yetmedi, GitHub'in IP'si icin de ayni hatayi verdi). Gercek cozum:
    # oturum acilmis bir YouTube hesabinin cookie'si (cookies.txt,
    # GRINDORIUM_YOUTUBE_COOKIES_B64 GitHub secret'indan build_config.py ile
    # bulut runner'inda olusturulur) + JS meydan okuma cozucu (deno,
    # --remote-components ejs:github ile indirilir, workflow'da kurulu
    # olmali). Cookie varsa once onu dener (en guvenilir, tam kalite),
    # yoksa/basarisiz olursa android client'a (dusuk kalite ama cookie'siz
    # calisir), sonra varsayilana duser.
    client_attempts = []
    if COOKIES_FILE.exists():
        client_attempts.append([
            "--cookies", str(COOKIES_FILE),
            "--js-runtimes", "deno",
            "--remote-components", "ejs:github",
        ])
    client_attempts.append(["--extractor-args", "youtube:player_client=android"])
    client_attempts.append([])
    result = None
    for extra_args in client_attempts:
        cmd = base_cmd + extra_args + [url]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            logger.error("Download timed out for %s", video_id)
            return None, None
        if result.returncode == 0:
            break
        logger.warning("yt-dlp denemesi basarisiz (%s): %s", extra_args or "varsayilan client", result.stderr[-400:])
    if result.returncode != 0:
        logger.error("yt-dlp failed for %s: %s", video_id, result.stderr[-800:])
        return None, None

    video_path = out_dir / f"{video_id}.mp4"
    info_path = out_dir / f"{video_id}.info.json"
    if not video_path.exists():
        candidates = list(out_dir.glob(f"{video_id}.*"))
        candidates = [c for c in candidates if c.suffix in (".mp4", ".mkv", ".webm")]
        if not candidates:
            logger.error("Downloaded file not found for %s", video_id)
            return None, None
        video_path = candidates[0]

    meta = {"id": video_id, "title": "", "description": "", "tags": [], "duration": 0}
    if info_path.exists():
        try:
            info = json.loads(info_path.read_text(encoding="utf-8"))
            meta["title"] = info.get("title", "")
            meta["description"] = info.get("description", "")
            meta["tags"] = info.get("tags", []) or []
            meta["duration"] = info.get("duration", 0) or 0
        except json.JSONDecodeError:
            logger.warning("Could not parse info json for %s", video_id)
    video_path = ensure_h264(video_path, logger)
    return str(video_path), meta


def ensure_h264(video_path, logger):
    """X, Facebook ve Instagram H.264 + AAC ister. Degilse ffmpeg ile cevir."""
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=codec_name", "-of", "csv=p=0", str(video_path)],
        capture_output=True, text=True)
    codec = probe.stdout.strip()
    if codec == "h264":
        return video_path
    logger.info("Codec %s, H.264'e ceviriliyor: %s", codec, video_path)
    out = Path(str(video_path)).with_name(Path(str(video_path)).stem + "_h264.mp4")
    conv = subprocess.run(
        ["ffmpeg", "-y", "-i", str(video_path), "-c:v", "libx264", "-preset", "fast",
         "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", str(out)],
        capture_output=True, text=True, timeout=1800)
    if conv.returncode != 0 or not out.exists():
        logger.error("ffmpeg donusum hatasi: %s", conv.stderr[-400:])
        return video_path
    return out
