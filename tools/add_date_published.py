"""
Adds datePublished to Article JSON-LD schema in writings/*.html pages.
Uses git first-commit date as the published date.
Run from repo root: python tools/add_date_published.py
Optional: --dry-run to preview, --only filename to process one file.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WRITINGS_DIR = REPO_ROOT / "writings"


def git_first_commit_date(filepath):
    rel = filepath.relative_to(REPO_ROOT)
    result = subprocess.run(
        ["git", "log", "--follow", "--diff-filter=A",
         "--format=%ad", "--date=format:%Y-%m-%d", "--", str(rel)],
        capture_output=True, text=True, cwd=REPO_ROOT
    )
    date = result.stdout.strip().splitlines()
    return date[0] if date else ""


def process_file(filepath, dry_run=False):
    text = filepath.read_text(encoding="utf-8")

    # Find Article JSON-LD block
    pattern = re.compile(
        r'(<script type="application/ld\+json">\s*)'
        r'(\{[^<]*?"@type"\s*:\s*"Article"[^<]*?\})'
        r'(\s*</script>)',
        re.DOTALL
    )
    match = pattern.search(text)
    if not match:
        return "SKIP_NO_ARTICLE"

    raw_json = match.group(2)
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        return "SKIP_INVALID_JSON"

    if "datePublished" in data:
        return "SKIP_ALREADY_HAS_DATE"

    date = git_first_commit_date(filepath)
    if not date:
        return "SKIP_NO_GIT_DATE"

    data["datePublished"] = date
    new_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    new_block = match.group(1) + new_json + match.group(3)
    new_text = text[:match.start()] + new_block + text[match.end():]

    if dry_run:
        return f"DRY_RUN date={date}"

    filepath.write_text(new_text, encoding="utf-8")
    return f"OK date={date}"


def main():
    dry_run = "--dry-run" in sys.argv
    only = None
    if "--only" in sys.argv:
        idx = sys.argv.index("--only")
        only = sys.argv[idx + 1]

    files = sorted(WRITINGS_DIR.glob("*.html"))
    if only:
        files = [f for f in files if f.name == only]

    updated = 0
    skipped = 0
    for f in files:
        result = process_file(f, dry_run=dry_run)
        print(f"  {f.name}: {result}")
        if result.startswith("OK"):
            updated += 1
        else:
            skipped += 1

    print(f"\nToplam: {updated} guncellendi, {skipped} atlandi")


if __name__ == "__main__":
    main()
