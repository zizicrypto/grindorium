"""
Grindorium Pinterest pin registry uretici (2026-07-11).
quotes_data.json (363 soz) + results_data.json (117 test sonuc karti) verilerini
okuyup, her pin icin gerekli TUM meta veriyi (baslik, aciklama, board, hedef link,
gorsel yolu) tek bir registry dosyasinda birlestirir:
  C:\\Users\\Ali\\grindorium\\engagement\\pinterest_registry.json

Bu script SADECE BIR KEZ (veya veri kaynaklari degisince) calistirilir. Engagement
rutini gece bu registry'den sirayla "posted": false olan kayitlari alip pinler,
posted=true + posted_date + pin_url ile isaretler. Registry siradan silinmez.

Sira: sozler ve test kartlari, gunluk "birkac pin karisik soz+kart" hedefine uygun
olacak sekilde ORANTILI ARALIKLANDIRILMIS (363 soz : 117 kart = ~3.1:1), yani
registry'nin basindan itibaren sirayla N tane alindiginda dogal olarak karisik cikar.
"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BASE)

QUOTES_JSON = os.path.join(BASE, "quotes_data.json")
RESULTS_JSON = os.path.join(BASE, "results_data.json")
QUOTES_IMG_DIR = os.path.join(BASE, "pinterest_assets", "quotes")
RESULTS_IMG_DIR = os.path.join(BASE, "pinterest_assets", "results")
OUT_PATH = os.path.join(REPO_ROOT, "engagement", "pinterest_registry.json")

SITE = "https://grindorium.org"
YOUTUBE_CHANNEL = "https://www.youtube.com/@Grindorium"

# Hedef link karisimi (2026-07-11, Ali'nin talebiyle eklendi): sozler ve test
# kartlari ARADA BIR YouTube kanaline, cogunlukla kendi sayfasina (soz->anasayfa,
# kart->kendi test sayfasi) link versin. Oran: her 3 kayittan 1'i YouTube (2:1).
# Deterministik (index-bazli), Math.random() gibi seed sorunlarindan kacinmak icin
# ve ayni girdiyle her calistirmada AYNI sonucu vermesi icin.
YOUTUBE_EVERY_NTH = 3  # index % 3 == 2 olan (0-index'te her 3.) kayit YouTube'a gider


def pick_destination(index_within_type, own_url):
    if index_within_type % YOUTUBE_EVERY_NTH == (YOUTUBE_EVERY_NTH - 1):
        return YOUTUBE_CHANNEL
    return own_url

# results_data.json'daki slug -> gercek dosya adi (tireler kaldirilmis, repo dosya
# adlandirma konvansiyonuyla birebir eslesir, 2026-07-11'de dosya listesiyle DOGRULANDI)
SLUG_TO_FILE = {
    "anxiety": "grindorium-anxiety.html",
    "attachment": "grindorium-attachment.html",
    "burnout": "grindorium-burnout.html",
    "discipline": "grindorium-discipline.html",
    "emotional-maturity": "grindorium-emotionalmaturity.html",
    "loneliness": "grindorium-loneliness.html",
    "numbness": "grindorium-numbness.html",
    "people-pleasing": "grindorium-peoplepleasing.html",
    "perfectionism": "grindorium-perfectionism.html",
    "procrastination": "grindorium-procrastination.html",
    "self-esteem": "grindorium-selfesteem.html",
    "self-sabotage": "grindorium-selfsabotage.html",
    "stress": "grindorium-stress.html",
}

QUOTE_BOARD = "Grindorium Quotes"
RESULT_BOARD = "Grindorium Self-Tests"


def build_quote_entries():
    quotes = json.load(open(QUOTES_JSON, encoding="utf-8"))
    entries = []
    for i, q in enumerate(quotes, start=1):
        img_name = f"quote_{i:03d}.png"
        img_path = os.path.join(QUOTES_IMG_DIR, img_name)
        text = q["text"]
        source = q.get("source", "Grindorium")
        title = text if len(text) <= 100 else text[:97].rsplit(" ", 1)[0] + "..."
        description = (
            f'"{text}" {source}. '
            f"A short reminder from Grindorium, a quiet space for burnout, focus, "
            f"and self-awareness."
        )
        entries.append({
            "id": f"quote_{i:03d}",
            "type": "quote",
            "image_path": img_path,
            "title": title,
            "description": description,
            "board": QUOTE_BOARD,
            "destination_url": pick_destination(i - 1, f"{SITE}/"),
            "posted": False,
            "posted_date": None,
            "pin_url": None,
        })
    return entries


def build_result_entries():
    results = json.load(open(RESULTS_JSON, encoding="utf-8"))
    entries = []
    for idx, r in enumerate(results):
        slug = r["slug"]
        key = r["key"]
        img_name = f"{slug}_{key}.png"
        img_path = os.path.join(RESULTS_IMG_DIR, img_name)
        test_name = r["test"]
        result_type = r["type"]
        tagline = r["tagline"]
        title = f"{test_name}: {result_type}"
        description = (
            f'{tagline} This is one possible result on the Grindorium {test_name}. '
            f"Take the free test to see where you land."
        )
        file_name = SLUG_TO_FILE.get(slug)
        if not file_name:
            raise ValueError(f"Bilinmeyen slug, SLUG_TO_FILE'a eklenmeli: {slug}")
        entries.append({
            "id": f"{slug}_{key}",
            "type": "result",
            "image_path": img_path,
            "title": title,
            "description": description,
            "board": RESULT_BOARD,
            "destination_url": pick_destination(idx, f"{SITE}/{file_name}"),
            "posted": False,
            "posted_date": None,
            "pin_url": None,
        })
    return entries


def interleave(quotes, results):
    """363 soz + 117 kart ~3.1:1 oranla, listenin basindan itibaren siradan
    alindiginda dogal olarak karisik cikacak sekilde aralar."""
    out = []
    qi, ri = 0, 0
    ratio = len(quotes) / len(results)
    next_result_at = ratio
    i = 0
    while qi < len(quotes) or ri < len(results):
        i += 1
        if ri < len(results) and i >= next_result_at:
            out.append(results[ri])
            ri += 1
            next_result_at += ratio
        elif qi < len(quotes):
            out.append(quotes[qi])
            qi += 1
        elif ri < len(results):
            out.append(results[ri])
            ri += 1
    return out


def main():
    quotes = build_quote_entries()
    results = build_result_entries()

    missing_imgs = [e["id"] for e in quotes + results if not os.path.isfile(e["image_path"])]
    if missing_imgs:
        print(f"UYARI: {len(missing_imgs)} gorsel dosyasi bulunamadi: {missing_imgs[:10]}...")

    combined = interleave(quotes, results)

    # ONEMLI: registry zaten varsa, GERCEKTEN pinlenmis (posted=true) kayitlar
    # OLDUGU GIBI KORUNUR (o pin zaten o linkle/basaligiyla yayinda, gecmisi
    # degistiremeyiz). Henuz pinlenmemis (posted=false) kayitlar ise YENIDEN
    # HESAPLANIR - boylece link-karisimi/metin gibi mantik degisiklikleri
    # henuz atilmamis pinlere otomatik yansir, ama yayinlanmis olanlara dokunulmaz.
    if os.path.isfile(OUT_PATH):
        with open(OUT_PATH, encoding="utf-8") as f:
            existing = {e["id"]: e for e in json.load(f)}
        merged = []
        for e in combined:
            old = existing.get(e["id"])
            if old and old.get("posted"):
                merged.append(old)
            else:
                merged.append(e)
        new_ids = [e["id"] for e in combined if e["id"] not in existing]
        removed_ids = [eid for eid in existing if eid not in {e["id"] for e in combined}]
        combined = merged
        if new_ids:
            print(f"YENI eklenen {len(new_ids)} kayit: {new_ids[:10]}...")
        if removed_ids:
            print(f"UYARI: kaynak veriden kaldirilmis ama registry'de hala duran "
                  f"{len(removed_ids)} kayit var (silinmedi, sadece bilgi): {removed_ids[:10]}")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=1)

    posted_count = sum(1 for e in combined if e["posted"])
    print(f"Yazildi: {OUT_PATH}")
    print(f"Toplam: {len(combined)} pin ({len(quotes)} soz + {len(results)} test karti), {posted_count} zaten pinlenmis")
    print(f"Boardlar: '{QUOTE_BOARD}', '{RESULT_BOARD}'")


if __name__ == "__main__":
    main()
