"""
AI rewriter. Sends the original YouTube metadata to the Claude API and gets
platform specific captions back as JSON. Any failure falls through to the
fallback formatter so the pipeline never stops.
"""
import json

import requests

from utils import fallback_formatter

API_URL = "https://api.anthropic.com/v1/messages"

PROMPT_TEMPLATE = """You write social media captions for Grindorium, a self-awareness brand.
Voice: quiet, direct, honest. No hype, no emojis in body text, no exclamation marks.
Audience: US first, then global. English only. Never use the em dash character anywhere.

Original YouTube video:
Title: {title}
Description: {description}
Tags: {tags}

Produce captions adapted for each platform. Respond with ONLY a JSON object, no markdown fences, with exactly these keys:
{{
  "instagram": {{"caption": "max 2200 chars, hook first line, link grindorium.org, then up to 30 hashtags on their own lines"}},
  "tiktok": {{"caption": "max 2200 chars, short and direct, 4 to 8 hashtags"}},
  "facebook": {{"caption": "title line, then description, then 3 to 5 hashtags"}},
  "twitter": {{"caption": "max 270 chars including 2 or 3 hashtags"}},
  "pinterest": {{"title": "max 95 chars", "description": "max 480 chars with grindorium.org mention"}}
}}"""


def rewrite_for_platforms(meta, config, logger):
    """Returns dict of platform captions. Always returns something usable."""
    claude_cfg = config.get("claude", {})
    if not claude_cfg.get("enabled") or not claude_cfg.get("api_key") or "YOUR_" in claude_cfg.get("api_key", ""):
        logger.info("Claude disabled or no key. Using fallback formatter.")
        return fallback_formatter.build_all(meta)

    prompt = PROMPT_TEMPLATE.format(
        title=meta.get("title", ""),
        description=(meta.get("description", "") or "")[:1500],
        tags=", ".join(meta.get("tags", [])[:20]),
    )
    try:
        resp = requests.post(
            API_URL,
            timeout=90,
            headers={
                "x-api-key": claude_cfg["api_key"],
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": claude_cfg.get("model", "claude-sonnet-4-20250514"),
                "max_tokens": 2000,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        if resp.status_code == 429:
            logger.warning("Claude rate limited. Using fallback.")
            return fallback_formatter.build_all(meta)
        resp.raise_for_status()
        data = resp.json()
        text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        text = text.replace("```json", "").replace("```", "").strip()
        captions = json.loads(text)
        cleaned = _validate(captions, meta, logger)
        logger.info("Claude captions generated for %s", meta.get("id"))
        return cleaned
    except (requests.RequestException, json.JSONDecodeError, KeyError, ValueError) as exc:
        logger.warning("Claude rewrite failed (%s). Using fallback.", exc)
        return fallback_formatter.build_all(meta)


def _validate(captions, meta, logger):
    """Enforce hard limits and fill any missing platform from fallback."""
    fb = fallback_formatter.build_all(meta)
    out = {}
    for platform in ("instagram", "tiktok", "facebook", "twitter", "pinterest"):
        item = captions.get(platform)
        if not item:
            out[platform] = fb[platform]
            continue
        if platform == "pinterest":
            title = str(item.get("title", ""))[:100]
            desc = str(item.get("description", ""))[:500]
            out[platform] = {"title": title or fb["pinterest"]["title"],
                             "description": desc or fb["pinterest"]["description"]}
        else:
            cap = str(item.get("caption", "")).replace("\u2014", ". ").replace("\u2013", "-")
            limit = 280 if platform == "twitter" else 2200
            if len(cap) > limit:
                cap = cap[:limit - 3].rsplit(" ", 1)[0] + "..."
            out[platform] = {"caption": cap or fb[platform]["caption"]}
    return out
