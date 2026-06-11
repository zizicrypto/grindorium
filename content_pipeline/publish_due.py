"""
Scheduled publisher. Runs weekly in GitHub Actions. Takes staged drafts whose
publish_date is due, builds the final pages from the live site templates, and
integrates everything: page file, listing/hub card, worker route, sitemap
entry. Validates site integrity before exiting. Exits 0 with no changes when
nothing is due.

Usage: python content_pipeline/publish_due.py [--max 1] [--force-slug SLUG]
"""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PIPE = Path(__file__).resolve().parent
STAGED = PIPE / "staged"
CAL = PIPE / "calendar.json"

ARTICLE_TEMPLATE = REPO / "writings" / "overstimulation.html"
WIKI_TEMPLATE = REPO / "grindorium-wiki-burnout.html"

TEST_LABELS = {
    "/burnout": "Burnout Test", "/anxiety": "Anxiety Test", "/stress": "Stress Test",
    "/numbness": "Emotional Numbness Test", "/attachment": "Attachment Style Test",
    "/discipline": "Discipline Test", "/perfectionism": "Perfectionism Test",
    "/people-pleasing": "People Pleasing Test", "/loneliness": "Loneliness Test",
    "/self-sabotage": "Self-Sabotage Test", "/emotional-maturity": "Emotional Maturity Test",
    "/self-esteem": "Self-Esteem Test", "/procrastination": "Procrastination Test",
}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# ---------------- article ----------------

def build_article(d):
    tpl = ARTICLE_TEMPLATE.read_text(encoding="utf-8")
    slug, title, desc = d["slug"], d["title"], d["content"]["meta_description"]
    h = tpl
    h = h.replace("Overstimulation | Grindorium", f"{esc(title)} | Grindorium")
    h = re.sub(r'(<meta name="description" content=")[^"]*(")', lambda m: m.group(1) + esc(desc) + m.group(2), h)
    h = h.replace("https://grindorium.org/writings/overstimulation", f"https://grindorium.org/writings/{slug}")
    h = re.sub(r'(<meta property="og:title" content=")[^"]*(")', lambda m: m.group(1) + esc(title) + m.group(2), h)
    h = re.sub(r'(<meta property="og:description" content=")[^"]*(")', lambda m: m.group(1) + esc(desc) + m.group(2), h)
    h = re.sub(r'("headline":")[^"]*(")', lambda m: m.group(1) + title.replace('"', "'") + m.group(2), h, count=1)
    h = re.sub(r'("description":")[^"]*(")', lambda m: m.group(1) + desc.replace('"', "'") + m.group(2), h, count=1)
    h = h.replace("<h1>Overstimulation</h1>", f"<h1>{esc(title)}</h1>")
    body = "\n".join(f"    <p>{esc(p)}</p>" for p in d["content"]["paragraphs"])
    h = re.sub(r'(<div class="article-body">).*?(</div>)', lambda m: m.group(1) + "\n" + body + "\n  " + m.group(2), h, count=1, flags=re.S)
    links = "".join(
        f'<a href="{r}" style="display:inline-block;padding:8px 14px;border:1px solid rgba(126,184,232,0.08);'
        f'color:#8aa0b8;text-decoration:none;font-size:10px;letter-spacing:0.06em;margin:4px;">{TEST_LABELS.get(r, r)}</a>'
        for r in d["related"] if r in TEST_LABELS)
    h = re.sub(r'(<div>)<a href="/burnout".*?(</div>)', lambda m: m.group(1) + links + m.group(2), h, count=1, flags=re.S)
    (REPO / "writings" / f"{slug}.html").write_text(h, encoding="utf-8")


def card_article(d):
    idx = REPO / "writings" / "index.html"
    h = idx.read_text(encoding="utf-8")
    if f'href="/writings/{d["slug"]}"' in h:
        return
    month = date.fromisoformat(d["publish_date"]).strftime("%b %Y")
    card = (f'    <a class="post-card" data-type="essay" href="/writings/{d["slug"]}">\n'
            f'      <div class="post-card-body">\n'
            f'        <div class="post-meta"><span class="post-type">Essay</span><span class="post-date">{month}</span><span class="post-read">3 min read</span></div>\n'
            f'        <div class="post-title">{esc(d["title"])}</div>\n'
            f'        <div class="post-excerpt">{esc(d["content"]["excerpt"])}</div>\n'
            f'        <div class="post-arrow">\u2197</div>\n      </div>\n    </a>\n\n')
    m = re.search(r'<a class="post-card"', h)
    h = h[:m.start()] + card + h[m.start():]
    idx.write_text(h, encoding="utf-8")


# ---------------- wiki ----------------

def build_wiki(d):
    tpl = WIKI_TEMPLATE.read_text(encoding="utf-8")
    slug, title, desc = d["slug"], d["title"], d["content"]["meta_description"]
    h = tpl
    h = re.sub(r"<title>[^<]*</title>", f"<title>{esc(title)} | Grindorium Wiki</title>", h, count=1)
    h = re.sub(r'(<meta name="description" content=")[^"]*(")', lambda m: m.group(1) + esc(desc) + m.group(2), h)
    h = h.replace("https://grindorium.org/wiki/burnout", f"https://grindorium.org/wiki/{slug}")
    h = re.sub(r'(<meta property="og:title" content=")[^"]*(")', lambda m: m.group(1) + esc(title) + m.group(2), h)
    h = re.sub(r'(<meta property="og:description" content=")[^"]*(")', lambda m: m.group(1) + esc(desc) + m.group(2), h)
    h = re.sub(r'("headline":")[^"]*(")', lambda m: m.group(1) + title.replace('"', "'") + m.group(2), h, count=1)
    h = re.sub(r'("description":")[^"]*(")', lambda m: m.group(1) + desc.replace('"', "'") + m.group(2), h, count=1)
    h = re.sub(r"<h1[^>]*>.*?</h1>", lambda m: re.sub(r">(.*?)</h1>", f">{esc(title)}</h1>", m.group(0), flags=re.S), h, count=1, flags=re.S)

    parts = []
    for p in d["content"]["intro"]:
        parts.append(f"    <p>{esc(p)}</p>")
    for sec in d["content"]["sections"]:
        parts.append(f"    <h2>{esc(sec['title'])}</h2>")
        for p in sec.get("paragraphs", []):
            parts.append(f"    <p>{esc(p)}</p>")
        if sec.get("bullets"):
            parts.append("    <ul>")
            for b in sec["bullets"]:
                parts.append(f"      <li>{esc(b)}</li>")
            parts.append("    </ul>")
    body = "\n".join(parts)
    h = re.sub(r'(<div class="wiki-body">).*?(\n  </div>)', lambda m: m.group(1) + "\n" + body + m.group(2), h, count=1, flags=re.S)
    (REPO / f"grindorium-wiki-{slug}.html").write_text(h, encoding="utf-8")


def card_wiki(d):
    hub = REPO / "grindorium-wiki.html"
    h = hub.read_text(encoding="utf-8")
    if f'href="/wiki/{d["slug"]}"' in h:
        return
    card = (f'<a href="/wiki/{d["slug"]}" class="wiki-card"><div class="wiki-card-tag">Mental health</div>'
            f'<div class="wiki-card-title">{esc(d["title"])}</div>'
            f'<div class="wiki-card-desc">{esc(d["content"]["hub_desc"])}</div></a>\n')
    m = re.search(r'<a href="/wiki/[a-z-]+" class="wiki-card">', h)
    h = h[:m.start()] + card + h[m.start():]
    hub.write_text(h, encoding="utf-8")


# ---------------- shared integration ----------------

def add_route(d):
    w_path = REPO / "_worker.js"
    w = w_path.read_text(encoding="utf-8")
    if d["type"] == "article":
        line = f"      '/writings/{d['slug']}': '/writings/{d['slug']}.html',"
    else:
        line = f"      '/wiki/{d['slug']}': '/grindorium-wiki-{d['slug']}.html',"
    if line.strip() in w:
        return
    anchor = "      '/privacy': '/privacy/index.html',"
    w = w.replace(anchor, line + "\n" + anchor, 1)
    w_path.write_text(w, encoding="utf-8")


def add_sitemap(d):
    s_path = REPO / "sitemap.xml"
    s = s_path.read_text(encoding="utf-8")
    loc = (f"https://grindorium.org/writings/{d['slug']}" if d["type"] == "article"
           else f"https://grindorium.org/wiki/{d['slug']}")
    if loc + "<" in s:
        return
    entry = f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{date.today().isoformat()}</lastmod>\n  </url>\n"
    s_path.write_text(s.replace("</urlset>", entry + "</urlset>"), encoding="utf-8")


def validate():
    import xml.etree.ElementTree as ET
    problems = []
    try:
        ET.parse(REPO / "sitemap.xml")
    except ET.ParseError as e:
        problems.append(f"sitemap.xml BOZUK: {e}")
    w = (REPO / "_worker.js").read_text(encoding="utf-8")
    if w.count("{") != w.count("}"):
        problems.append("_worker.js parantez dengesi bozuk")
    for f in ("writings/index.html", "grindorium-wiki.html"):
        t = (REPO / f).read_text(encoding="utf-8")
        if not t.rstrip().endswith("</html>"):
            problems.append(f"{f} dosya sonu bozuk")
        if "\u2014" in t:
            problems.append(f"{f} icinde em dash var")
    if problems:
        print("DOGRULAMA HATASI, yayin iptal:")
        for p in problems:
            print("  -", p)
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=1)
    ap.add_argument("--force-slug", default=None)
    args = ap.parse_args()

    cal = json.loads(CAL.read_text(encoding="utf-8"))
    today = date.today().isoformat()
    published = 0

    for item in cal["items"]:
        if published >= args.max:
            break
        if args.force_slug:
            if item["slug"] != args.force_slug:
                continue
        elif item["status"] != "staged" or item["publish_date"] > today:
            continue
        draft_path = STAGED / f"{item['slug']}.json"
        if not draft_path.exists():
            print(f"UYARI: staged taslak yok: {item['slug']}")
            continue
        d = json.loads(draft_path.read_text(encoding="utf-8"))
        # icerik em dash son kontrol
        raw = json.dumps(d, ensure_ascii=False)
        if "\u2014" in raw:
            print(f"UYARI: {item['slug']} taslaginda em dash var, temizleniyor")
            d = json.loads(raw.replace("\u2014", ", "))
        print(f"Yayinlaniyor [{d['type']}]: {d['title']} ({item['publish_date']})")
        if d["type"] == "article":
            build_article(d)
            card_article(d)
        else:
            build_wiki(d)
            card_wiki(d)
        add_route(d)
        add_sitemap(d)
        item["status"] = "published"
        item["published_on"] = today
        draft_path.rename(STAGED / f"{item['slug']}.published.json")
        published += 1

    if published:
        validate()
        CAL.write_text(json.dumps(cal, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"\n{published} parca yayinlandi ve dogrulandi.")
    else:
        print("Bugun yayini gelen parca yok.")


if __name__ == "__main__":
    main()
