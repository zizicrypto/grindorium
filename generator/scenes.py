"""
Grindorium scene engine.
13 themed, fully procedural night scenes. Every image is generated, owned,
deterministic, and unique per seed. No stock photos, no external assets.

Each scene returns a 1000x1500 RGB image ready for the text overlay.
"""
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1000, 1500


def _rng(seed):
    return random.Random(seed)


def _vgrad(top, bottom, curve=1.0):
    t = (np.linspace(0, 1, H) ** curve)[:, None, None]
    a = np.array(top, dtype=float)[None, None, :]
    b = np.array(bottom, dtype=float)[None, None, :]
    arr = a + (b - a) * t
    return np.repeat(arr, W, axis=1)


def _to_img(arr):
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def _glow(img, cx, cy, r, color, alpha):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color + (alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(r * 0.55))
    img.paste(layer, (0, 0), layer)


def _stars(d, rng, n, ymax, bright=(150, 230)):
    for _ in range(n):
        x, y = rng.randrange(W), rng.randrange(int(ymax))
        b = rng.randint(*bright)
        s = rng.choice([1, 1, 1, 2])
        d.ellipse([x - s, y - s, x + s, y + s], fill=(b, b, min(255, b + 18)))


def _moon(img, d, rng, area=(0.18, 0.85), ry=(0.15, 0.26), rr=(34, 52)):
    mx = W * rng.uniform(*area)
    my = H * rng.uniform(*ry)
    r = rng.randint(*rr)
    _glow(img, mx, my, r * 3, (200, 215, 235), 40)
    d.ellipse([mx - r, my - r, mx + r, my + r], fill=(222, 228, 236))
    return mx, my, r


def _ridge(d, rng, base, var, color, step=(40, 90)):
    pts = [(0, H)]
    y = H * base
    x = 0
    while x <= W:
        y += rng.randint(-var, var)
        y = max(H * (base - 0.10), min(H * (base + 0.07), y))
        pts.append((x, y))
        x += rng.randint(*step)
    pts.append((W, H))
    d.polygon(pts, fill=color)


def _fog_band(img, y0, y1, color, alpha, blur=60):
    fog = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fog)
    fd.rectangle([0, y0, W, y1], fill=color + (alpha,))
    fog = fog.filter(ImageFilter.GaussianBlur(blur))
    img.paste(fog, (0, 0), fog)


def _pine(d, x, base_y, h, color, rng):
    wdt = h * rng.uniform(0.34, 0.46)
    layers = 4
    for i in range(layers):
        ly = base_y - h * (i / layers)
        lw = wdt * (1 - i / (layers + 0.6))
        lh = h / layers * 1.5
        d.polygon([(x - lw / 2, ly), (x + lw / 2, ly), (x, ly - lh)], fill=color)
    d.rectangle([x - 3, base_y - 4, x + 3, base_y + 8], fill=color)


def _bare_tree(d, rng, x, base_y, h, color, lean=0.0):
    def branch(bx, by, ang, ln, depth, width):
        if depth == 0 or ln < 9:
            return
        x2 = bx + math.cos(ang) * ln
        y2 = by + math.sin(ang) * ln
        d.line([(bx, by), (x2, y2)], fill=color, width=max(1, int(width)))
        n = rng.choice([2, 2, 3])
        for _ in range(n):
            branch(x2, y2, ang + rng.uniform(-0.65, 0.65) + lean * 0.2, ln * rng.uniform(0.62, 0.78), depth - 1, width * 0.65)
    branch(x, base_y, -math.pi / 2 + lean, h * 0.38, 6, h * 0.045)


def _canopy_tree(d, rng, x, base_y, h, trunk, leaf):
    d.line([(x, base_y), (x, base_y - h * 0.45)], fill=trunk, width=int(h * 0.05))
    cx, cy = x, base_y - h * 0.55
    for _ in range(26):
        r = h * rng.uniform(0.10, 0.22)
        ox = rng.uniform(-h * 0.30, h * 0.30)
        oy = rng.uniform(-h * 0.22, h * 0.16)
        d.ellipse([cx + ox - r, cy + oy - r, cx + ox + r, cy + oy + r], fill=leaf)


# ------------------------------------------------------------------ scenes

def foggy_forest(seed):
    rng = _rng(seed)
    img = _to_img(_vgrad((11, 16, 26), (26, 36, 50), 1.4))
    d = ImageDraw.Draw(img)
    _stars(d, rng, rng.randint(40, 90), H * 0.35, (90, 150))
    rows = [(0.34, (24, 32, 46), 0.13), (0.43, (16, 22, 34), 0.16), (0.52, (9, 13, 22), 0.20)]
    for base, col, hs in rows:
        x = -30
        while x < W + 30:
            _pine(d, x, H * base, H * hs * rng.uniform(0.75, 1.15), col, rng)
            x += rng.randint(50, 130)
        _fog_band(img, int(H * base) - 70, int(H * base) + 10, (140, 158, 178), rng.randint(30, 48))
        d = ImageDraw.Draw(img)
    return img


def rain_window(seed):
    rng = _rng(seed)
    img = _to_img(_vgrad((9, 13, 24), (22, 30, 46), 1.2))
    # bokeh city lights behind glass
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    palette = [(126, 184, 232), (232, 200, 140), (190, 160, 220), (150, 210, 190)]
    for _ in range(rng.randint(26, 40)):
        x = rng.randrange(W)
        y = rng.randrange(int(H * 0.08), int(H * 0.50))
        r = rng.randint(12, 56)
        c = rng.choice(palette)
        ld.ellipse([x - r, y - r, x + r, y + r], fill=c + (rng.randint(26, 70),))
    layer = layer.filter(ImageFilter.GaussianBlur(26))
    img.paste(layer, (0, 0), layer)
    d = ImageDraw.Draw(img)
    # rain streaks on glass
    for _ in range(rng.randint(70, 110)):
        x = rng.randrange(W)
        y = rng.randrange(int(H * 0.62))
        ln = rng.randint(26, 120)
        drift = rng.randint(-6, 6)
        a = rng.randint(34, 80)
        d.line([(x, y), (x + drift, y + ln)], fill=(170, 195, 224), width=1)
        d.ellipse([x + drift - 2, y + ln - 2, x + drift + 2, y + ln + 2], fill=(190, 210, 232))
    img = img.filter(ImageFilter.GaussianBlur(0.4))
    return img


def storm_ocean(seed):
    rng = _rng(seed)
    img = _to_img(_vgrad((12, 15, 24), (8, 14, 24), 1.0))
    d = ImageDraw.Draw(img)
    # heavy clouds
    for _ in range(rng.randint(10, 16)):
        cx = rng.randrange(W)
        cy = rng.randrange(int(H * 0.22))
        r = rng.randint(80, 200)
        _glow(img, cx, cy, r, (30, 38, 54), rng.randint(60, 110))
    d = ImageDraw.Draw(img)
    # lightning sometimes
    if rng.random() < 0.7:
        x = rng.randrange(int(W * 0.2), int(W * 0.8))
        y = rng.randrange(40, int(H * 0.16))
        pts = [(x, y)]
        for _ in range(rng.randint(5, 8)):
            x += rng.randint(-46, 46)
            y += rng.randint(40, 90)
            pts.append((x, y))
        d.line(pts, fill=(232, 238, 250), width=2)
        _glow(img, pts[0][0], pts[0][1], 90, (200, 215, 240), 50)
        d = ImageDraw.Draw(img)
    # sea
    sea_y = int(H * 0.42)
    d.rectangle([0, sea_y, W, H], fill=(10, 16, 26))
    for k in range(14):
        y = sea_y + k * rng.randint(16, 26)
        if y > H * 0.60:
            break
        pts = []
        for x in range(0, W + 20, 24):
            pts.append((x, y + math.sin(x / rng.uniform(40, 90) + k) * rng.uniform(4, 14)))
        d.line(pts, fill=(40 + k * 2, 56 + k * 2, 78 + k * 2), width=1)
    # whitecaps
    for _ in range(rng.randint(14, 26)):
        x = rng.randrange(W)
        y = rng.randrange(sea_y + 10, int(H * 0.58))
        ln = rng.randint(14, 60)
        d.line([(x, y), (x + ln, y)], fill=(150, 168, 190), width=2)
    return img


def snowfall(seed):
    rng = _rng(seed)
    img = _to_img(_vgrad((14, 18, 30), (30, 38, 54), 1.3))
    d = ImageDraw.Draw(img)
    _ridge(d, rng, 0.44, 22, (22, 28, 42))
    x = -20
    while x < W + 20:
        _pine(d, x, H * rng.uniform(0.46, 0.52), H * rng.uniform(0.10, 0.16), (10, 15, 26), rng)
        x += rng.randint(70, 160)
    # ground
    d.rectangle([0, int(H * 0.54), W, H], fill=(16, 21, 32))
    # snow
    for _ in range(rng.randint(220, 320)):
        x = rng.randrange(W)
        y = rng.randrange(H)
        if y > H * 0.60 and rng.random() < 0.75:
            continue
        s = rng.choice([1, 1, 2, 2, 3])
        a = rng.randint(120, 230)
        d.ellipse([x - s, y - s, x + s, y + s], fill=(a, a, min(255, a + 10)))
    return img


def two_trees(seed):
    rng = _rng(seed)
    img = _to_img(_vgrad((14, 19, 33), (36, 44, 60), 1.3))
    d = ImageDraw.Draw(img)
    _stars(d, rng, rng.randint(120, 200), H * 0.45)
    _moon(img, d, rng)
    d = ImageDraw.Draw(img)
    ground = int(H * 0.50)
    d.rectangle([0, ground, W, H], fill=(10, 14, 23))
    _ridge(d, rng, 0.50, 12, (10, 14, 23), step=(80, 140))
    # the distance between the two trees is the meaning
    gap = rng.uniform(0.16, 0.55)
    x1 = W * (0.5 - gap / 2)
    x2 = W * (0.5 + gap / 2)
    _bare_tree(d, rng, x1, ground, H * rng.uniform(0.26, 0.32), (7, 10, 17), lean=rng.uniform(0.0, 0.14))
    _bare_tree(d, rng, x2, ground, H * rng.uniform(0.24, 0.30), (7, 10, 17), lean=-rng.uniform(0.0, 0.14))
    _fog_band(img, ground - 40, ground + 20, (120, 140, 165), 24)
    return img


def lone_tree(seed):
    rng = _rng(seed)
    img = _to_img(_vgrad((13, 18, 31), (38, 46, 62), 1.4))
    d = ImageDraw.Draw(img)
    _stars(d, rng, rng.randint(150, 240), H * 0.45)
    _moon(img, d, rng, area=(0.55, 0.88))
    d = ImageDraw.Draw(img)
    ground = int(H * rng.uniform(0.48, 0.52))
    d.rectangle([0, ground, W, H], fill=(9, 13, 22))
    _ridge(d, rng, ground / H, 9, (9, 13, 22), step=(90, 160))
    _bare_tree(d, rng, W * rng.uniform(0.34, 0.58), ground, H * rng.uniform(0.28, 0.34), (6, 9, 16))
    return img


def mountains_moon(seed):
    rng = _rng(seed)
    img = _to_img(_vgrad((10, 16, 30), (40, 58, 86), 1.6))
    d = ImageDraw.Draw(img)
    _stars(d, rng, rng.randint(160, 240), H * 0.55)
    _moon(img, d, rng)
    d = ImageDraw.Draw(img)
    for col, base in [((20, 28, 44), 0.36), ((14, 20, 33), 0.44), ((8, 12, 22), 0.52)]:
        _ridge(d, rng, base, 34, col)
    _fog_band(img, int(H * 0.42), int(H * 0.52), (120, 140, 165), 40)
    return img


def still_lake(seed):
    rng = _rng(seed)
    img = _to_img(_vgrad((10, 15, 28), (18, 26, 40), 1.2))
    d = ImageDraw.Draw(img)
    _stars(d, rng, rng.randint(120, 200), H * 0.42)
    mx, my, mr = _moon(img, d, rng, area=(0.35, 0.65), ry=(0.10, 0.20))
    d = ImageDraw.Draw(img)
    water_y = int(H * 0.36)
    _ridge(d, rng, 0.34, 18, (10, 14, 24), step=(60, 110))
    # mirror water
    band_h = int(H * 0.13)
    top = img.crop((0, 0, W, water_y)).transpose(Image.FLIP_TOP_BOTTOM)
    top = top.resize((W, band_h))
    top = top.filter(ImageFilter.GaussianBlur(2.2))
    dark = Image.new("RGB", top.size, (6, 10, 18))
    top = Image.blend(top, dark, 0.42)
    img.paste(top, (0, water_y))
    d = ImageDraw.Draw(img)
    d.rectangle([0, water_y + band_h, W, H], fill=(7, 11, 19))
    _fog_band(img, water_y + band_h - 30, water_y + band_h + 30, (10, 16, 26), 120, blur=40)
    d = ImageDraw.Draw(img)
    # moon path on water
    for k in range(6):
        y = water_y + 12 + k * 12
        wdt = mr * (1.3 + k * 0.16) * rng.uniform(0.7, 1.0)
        a = max(10, 60 - k * 3)
        seg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(seg)
        sd.line([(mx - wdt / 2, y), (mx + wdt / 2, y)], fill=(210, 220, 235, a), width=2)
        img.paste(seg, (0, 0), seg)
    d.line([(0, water_y), (W, water_y)], fill=(60, 76, 98), width=1)
    return img


def city_lights(seed):
    rng = _rng(seed)
    img = _to_img(_vgrad((9, 12, 22), (20, 24, 38), 1.3))
    d = ImageDraw.Draw(img)
    _stars(d, rng, rng.randint(60, 110), H * 0.30, (80, 140))
    horizon = int(H * rng.uniform(0.42, 0.46))
    # skyline blocks
    x = -10
    while x < W + 10:
        bw = rng.randint(36, 110)
        bh = rng.randint(40, 220)
        d.rectangle([x, horizon - bh, x + bw, horizon], fill=(7, 10, 18))
        # windows: other people's lights
        for _ in range(int(bw * bh / 380)):
            wx = x + rng.randint(4, max(5, bw - 6))
            wy = horizon - rng.randint(6, max(7, bh - 6))
            if rng.random() < 0.5:
                c = rng.choice([(232, 206, 142), (126, 184, 232), (220, 180, 200)])
                d.rectangle([wx, wy, wx + 3, wy + 4], fill=c)
        x += bw + rng.randint(2, 14)
    # glow above city
    _glow(img, W * 0.5, horizon - 40, 320, (90, 110, 150), 36)
    d = ImageDraw.Draw(img)
    # dark foreground hill: the viewer stands outside
    _ridge(d, rng, 0.52, 14, (5, 8, 14), step=(100, 180))
    return img


def winding_road(seed):
    rng = _rng(seed)
    img = _to_img(_vgrad((10, 14, 26), (28, 34, 48), 1.4))
    d = ImageDraw.Draw(img)
    _stars(d, rng, rng.randint(130, 200), H * 0.5)
    _moon(img, d, rng, area=(0.15, 0.45))
    d = ImageDraw.Draw(img)
    _ridge(d, rng, 0.40, 22, (14, 19, 31))
    d.rectangle([0, int(H * 0.46), W, H], fill=(11, 15, 25))
    horizon_y = int(H * 0.40)
    # road that forks: one path fades
    cx = W * 0.5
    fork_y = H * rng.uniform(0.50, 0.54)
    bottom_w = W * rng.uniform(0.22, 0.30)
    top_w = 10
    road = (26, 32, 46)
    start_y = int(H * 0.62)
    d.polygon([(cx - bottom_w / 2, start_y), (cx + bottom_w / 2, start_y),
               (cx + top_w, fork_y), (cx - top_w, fork_y)], fill=road)
    end1 = (W * rng.uniform(0.18, 0.36), horizon_y)
    end2 = (W * rng.uniform(0.62, 0.82), horizon_y)
    d.polygon([(cx - top_w, fork_y), (cx + top_w, fork_y), (end1[0] + 5, end1[1]), (end1[0] - 5, end1[1])], fill=road)
    faded = (19, 24, 36)
    d.polygon([(cx - top_w, fork_y), (cx + top_w, fork_y), (end2[0] + 5, end2[1]), (end2[0] - 5, end2[1])], fill=faded)
    # center dashes
    y = start_y - 12
    while y > fork_y + 18:
        t = (start_y - y) / (start_y - fork_y)
        dw = max(2, 7 * (1 - t))
        d.line([(cx, y), (cx, y - 22 * (1 - t) - 8)], fill=(150, 165, 188), width=int(dw))
        y -= 56 * (1 - t) + 26
    return img


def dawn_horizon(seed):
    rng = _rng(seed)
    img = _to_img(_vgrad((12, 16, 30), (10, 14, 24), 1.0))
    # dawn glow at horizon
    horizon = int(H * rng.uniform(0.40, 0.44))
    glow_h = int(H * 0.30)
    arr = np.array(img, dtype=float)
    dawn = np.array([196, 138, 96], dtype=float)
    for y in range(horizon - glow_h, horizon):
        t = (y - (horizon - glow_h)) / glow_h
        arr[y] = arr[y] * (1 - 0.5 * t ** 2) + dawn * (0.5 * t ** 2)
    img = _to_img(arr)
    d = ImageDraw.Draw(img)
    _stars(d, rng, rng.randint(60, 110), H * 0.35, (80, 150))
    sun_x = W * rng.uniform(0.3, 0.7)
    _glow(img, sun_x, horizon, 140, (232, 168, 110), 70)
    d = ImageDraw.Draw(img)
    d.ellipse([sun_x - 30, horizon - 14, sun_x + 30, horizon + 46], fill=(238, 186, 128))
    d.rectangle([0, horizon, W, H], fill=(9, 12, 20))
    for k in range(9):
        y = horizon + 10 + k * 16
        a = max(20, 110 - k * 7)
        d.line([(sun_x - 40 - k * 8, y), (sun_x + 40 + k * 8, y)], fill=(120 + a // 3, 90 + a // 4, 70), width=1)
    _ridge(d, rng, 0.56, 10, (6, 9, 15), step=(110, 190))
    return img


def big_tree(seed):
    rng = _rng(seed)
    img = _to_img(_vgrad((11, 15, 27), (24, 30, 44), 1.3))
    d = ImageDraw.Draw(img)
    _stars(d, rng, rng.randint(130, 210), H * 0.55)
    _moon(img, d, rng, area=(0.62, 0.88), ry=(0.08, 0.16))
    d = ImageDraw.Draw(img)
    ground = int(H * 0.52)
    d.rectangle([0, ground, W, H], fill=(10, 14, 23))
    _ridge(d, rng, 0.52, 9, (10, 14, 23), step=(110, 190))
    _canopy_tree(d, rng, W * rng.uniform(0.38, 0.58), ground, H * rng.uniform(0.30, 0.36),
                 (12, 16, 26), (15, 21, 33))
    _fog_band(img, ground - 30, ground + 16, (120, 140, 165), 18)
    return img


def desert_dunes(seed):
    rng = _rng(seed)
    img = _to_img(_vgrad((12, 14, 26), (20, 22, 36), 1.2))
    d = ImageDraw.Draw(img)
    _stars(d, rng, rng.randint(200, 300), H * 0.45)
    _moon(img, d, rng, ry=(0.08, 0.18))
    d = ImageDraw.Draw(img)
    bases = [(0.36, (28, 26, 43)), (0.43, (21, 20, 35)), (0.50, (15, 14, 26)), (0.57, (9, 9, 18))]
    for base, col in bases:
        pts = [(0, H)]
        y = H * base
        x = 0
        while x <= W:
            y = H * base + math.sin(x / rng.uniform(160, 320) + rng.random() * 6) * H * 0.035
            pts.append((x, y))
            x += 24
        pts.append((W, H))
        d.polygon(pts, fill=col)
        # dune crest highlight
        d.line(pts[1:-1], fill=tuple(min(255, c + 16) for c in col), width=1)
    return img


SCENES = {
    "burnout": foggy_forest,
    "anxiety": rain_window,
    "stress": storm_ocean,
    "numbness": snowfall,
    "attachment": two_trees,
    "loneliness": lone_tree,
    "discipline": mountains_moon,
    "perfectionism": still_lake,
    "people-pleasing": city_lights,
    "self-sabotage": winding_road,
    "self-esteem": dawn_horizon,
    "emotional-maturity": big_tree,
    "procrastination": desert_dunes,
}
SCENE_ORDER = list(SCENES.values())
