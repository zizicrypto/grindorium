"""
Grindorium Pinterest image factory v2.
Fully owned procedural scene backgrounds + Grindorium typography.
  python factory_v2.py quotes | results | samples
"""
import json, math, zlib, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import scenes

BASE = Path(__file__).resolve().parent
FONTS = BASE / "fonts"
OUT = BASE / "pinterest_assets"
W, H = 1000, 1500

def font(n, s): return ImageFont.truetype(str(FONTS / n), s)
def lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
def hex_rgb(h): h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
def crc(s): return zlib.crc32(s.encode()) & 0xFFFFFFFF

def overlay_for_text(img):
    ov = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(ov)
    for y in range(H):
        t = y / H
        a = int(150 * (1 - t) ** 2 * 0.9)
        a = max(a, int(215 * max(0, t - 0.45) ** 1.3))
        a = max(a, 58)
        d.line([(0, y), (W, y)], fill=a)
    black = Image.new("RGB", (W, H), (5, 8, 14))
    return Image.composite(black, img, ov)

def spaced(d, y, txt, fnt, fill, sp):
    ws = [d.textlength(c, font=fnt) for c in txt]
    tot = sum(ws) + sp * (len(txt) - 1)
    x = (W - tot) / 2
    for c, w in zip(txt, ws):
        d.text((x, y), c, font=fnt, fill=fill)
        x += w + sp

def wrap(d, t, f, mw):
    out, cur = [], ""
    for w in t.split():
        tr = (cur + " " + w).strip()
        if d.textlength(tr, font=f) <= mw:
            cur = tr
        else:
            if cur: out.append(cur)
            cur = w
    if cur: out.append(cur)
    return out

def fit(d, text, max_w, max_h, start, minimum, lf, face):
    size = start
    while size >= minimum:
        f = font(face, size)
        lines = wrap(d, text, f, max_w)
        lh = int(size * lf)
        if len(lines) * lh <= max_h:
            return f, lines, lh
        size -= 4
    f = font(face, minimum)
    return f, wrap(d, text, f, minimum), int(minimum * lf)

def soft_text(d, xy, txt, fnt, fill, anchor="ma"):
    # ince golge: fotograf ustunde okunurluk
    x, y = xy
    d.text((x + 1, y + 2), txt, font=fnt, fill=(0, 0, 0), anchor=anchor)
    d.text((x, y), txt, font=fnt, fill=fill, anchor=anchor)

def make_quote(idx, q, path):
    seed = crc(f"quote|{idx}|{q['text'][:40]}")
    scene_fn = scenes.SCENE_ORDER[idx % len(scenes.SCENE_ORDER)]
    img = overlay_for_text(scene_fn(seed))
    d = ImageDraw.Draw(img)
    spaced(d, 96, "GRINDORIUM", font("SpaceMono-Regular.ttf", 26), (235, 242, 250), 10)
    spaced(d, 142, "DAILY QUOTE", font("SpaceMono-Regular.ttf", 21), (160, 178, 198), 8)
    qf, lines, lh = fit(d, q["text"], W - 200, int(H * 0.34), 76, 44, 1.32, "Cormorant-Light.ttf")
    qy = int(H * 0.62) - len(lines) * lh // 2
    d.line([(W // 2 - 22, qy - 50), (W // 2 + 22, qy - 50)], fill=(180, 200, 224), width=2)
    for ln in lines:
        soft_text(d, (W // 2, qy), ln, qf, (249, 251, 253))
        qy += lh
    qy += 38
    spaced(d, qy, q["source"].upper(), font("SpaceMono-Regular.ttf", 24), (192, 208, 226), 6)
    spaced(d, H - 116, "GRINDORIUM.ORG", font("SpaceMono-Regular.ttf", 23), (196, 210, 224), 5)
    soft_text(d, (W // 2, H - 72), "You are safe here.", font("Cormorant-Italic.ttf", 30), (172, 186, 202))
    img.save(path, "PNG")

def make_result(r, path):
    seed = crc(f"result|{r['slug']}|{r['key']}")
    scene_fn = scenes.SCENES.get(r["slug"], scenes.mountains_moon)
    img = overlay_for_text(scene_fn(seed))
    d = ImageDraw.Draw(img)
    accent = hex_rgb(r["accent"])
    spaced(d, 96, "GRINDORIUM", font("SpaceMono-Regular.ttf", 26), (235, 242, 250), 10)
    spaced(d, 142, (r["test"] + "  ·  RESULT").upper(), font("SpaceMono-Regular.ttf", 21), lerp(accent, (255, 255, 255), 0.35), 6)
    tf, tlines, tlh = fit(d, r["type"], W - 200, 280, 96, 58, 1.22, "Cormorant-Regular.ttf")
    block = len(tlines) * tlh
    ty = int(H * 0.58) - block // 2
    for ln in tlines:
        soft_text(d, (W // 2, ty), ln, tf, (250, 251, 253))
        ty += tlh
    ty += 30
    d.line([(W // 2 - 34, ty), (W // 2 + 34, ty)], fill=lerp(accent, (255, 255, 255), 0.15), width=2)
    ty += 40
    gf, glines, glh = fit(d, r["tagline"], W - 240, 220, 42, 30, 1.45, "Cormorant-Italic.ttf")
    for ln in glines:
        soft_text(d, (W // 2, ty), ln, gf, (214, 222, 232))
        ty += glh
    cta_y = H - 250
    cf = font("SpaceMono-Regular.ttf", 20)
    ct = "WHICH ONE ARE YOU?  TAKE THE FREE TEST"
    tw = sum(d.textlength(c, font=cf) for c in ct) + 3 * (len(ct) - 1)
    half = int(tw / 2) + 42
    d.rectangle([(W // 2 - half, cta_y), (W // 2 + half, cta_y + 78)], outline=lerp(accent, (255, 255, 255), 0.25), width=1)
    spaced(d, cta_y + 26, ct, cf, lerp(accent, (255, 255, 255), 0.55), 3)
    spaced(d, H - 116, ("GRINDORIUM.ORG/" + r["slug"]).upper(), font("SpaceMono-Regular.ttf", 23), (196, 210, 224), 5)
    soft_text(d, (W // 2, H - 72), "Free. No account needed.", font("Cormorant-Italic.ttf", 28), (168, 182, 198))
    img.save(path, "PNG")

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "samples"
    quotes = json.loads((BASE / "quotes_data.json").read_text(encoding="utf-8"))
    results = json.loads((BASE / "results_data.json").read_text(encoding="utf-8"))
    if mode in ("quotes", "samples"):
        qd = OUT / "quotes"; qd.mkdir(parents=True, exist_ok=True)
        picks = range(len(quotes)) if mode == "quotes" else [0, 46, 150, 300]
        for i in picks:
            make_quote(i, quotes[i], qd / f"quote_{i+1:03d}.png")
            if mode == "quotes" and (i + 1) % 25 == 0:
                print(f"quotes {i+1}/{len(quotes)}", flush=True)
        print("quotes done")
    if mode in ("results", "samples"):
        rd = OUT / "results"; rd.mkdir(parents=True, exist_ok=True)
        idxs = range(len(results)) if mode == "results" else [1, 22, 40, 64, 85, 100]
        for i in idxs:
            r = results[i]
            make_result(r, rd / f"{r['slug']}_{r['key']}.png")
            if mode == "results" and (i + 1) % 20 == 0:
                print(f"results {i+1}/{len(results)}", flush=True)
        print("results done")

if __name__ == "__main__":
    main()
