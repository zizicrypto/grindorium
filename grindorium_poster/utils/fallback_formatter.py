"""
Fallback formatter. Builds platform captions from the original YouTube
metadata with trimming and hashtag injection. Never writes new copy from
scratch, only reshapes what already exists.
"""

DEFAULT_TAGS = ["selfawareness", "psychology", "burnout", "mentalclarity", "grindorium"]
STICKLINE_TAGS = ["discipline", "mindset", "motivation", "selfimprovement", "grindorium"]


def _hashtags(meta, count, defaults=DEFAULT_TAGS):
    tags = []
    for t in meta.get("tags", []):
        clean = "".join(c for c in t if c.isalnum())
        if clean and clean.lower() not in [x.lower() for x in tags]:
            tags.append(clean)
        if len(tags) >= count:
            break
    for t in defaults:
        if len(tags) >= count:
            break
        if t not in tags:
            tags.append(t)
    return " ".join("#" + t for t in tags[:count])


def _trim(text, limit):
    text = (text or "").replace("\u2014", ". ").replace("\u2013", "-").strip()
    if len(text) <= limit:
        return text
    return text[:limit - 3].rsplit(" ", 1)[0] + "..."


def build_all(meta, content_type="grindorium"):
    defaults = STICKLINE_TAGS if content_type == "stickline" else DEFAULT_TAGS
    title = meta.get("title", "").strip()
    desc = meta.get("description", "").strip()
    first_para = desc.split("\n\n")[0] if desc else ""

    ig_body = f"{title}\n\n{_trim(first_para, 1500)}\n\ngrindorium.org\n\n{_hashtags(meta, 30, defaults)}"
    tt_body = f"{title}\n\n{_trim(first_para, 1600)}\n\n{_hashtags(meta, 6, defaults)}"
    fb_body = f"{title}\n\n{_trim(desc, 1800)}\n\n{_hashtags(meta, 4, defaults)}"
    tw_text = _trim(title, 230) + "\n" + _hashtags(meta, 3, defaults)

    return {
        "instagram": {"caption": _trim(ig_body, 2200)},
        "tiktok": {"caption": _trim(tt_body, 2200)},
        "facebook": {"caption": fb_body},
        "twitter": {"caption": _trim(tw_text, 280)},
        "pinterest": {
            "title": _trim(title, 100),
            "description": _trim(f"{first_para} More at grindorium.org", 500),
        },
    }
