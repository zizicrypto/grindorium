"""
Adds Copy button after address box in Support card on all 13 test pages.
Run from repo root: python tools/add_copy_btn_tests.py [--dry-run] [--only filename]
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

ADDR_BOX = '      <div onclick="grndCopyAddr(this)" title="Click to copy" style="background:#444441;font-family:\'Space Mono\',monospace;font-size:9px;color:#FAEEDA;word-break:break-all;padding:10px 12px;cursor:pointer;margin-bottom:6px;text-align:left;border:1px solid rgba(250,238,218,0.08);">0x467eff5639e0db4d8b333df463facaa997bc8aac</div>'

ADDR_BOX_WITH_BTN = ('      <div onclick="grndCopyAddr(this)" title="Click to copy" style="background:#444441;font-family:\'Space Mono\',monospace;font-size:9px;color:#FAEEDA;word-break:break-all;padding:10px 12px;cursor:pointer;margin-bottom:4px;text-align:left;border:1px solid rgba(250,238,218,0.08);">0x467eff5639e0db4d8b333df463facaa997bc8aac</div>\n'
'      <button onclick="(function(b){var a=b.previousElementSibling.textContent.trim();(navigator.clipboard?navigator.clipboard.writeText(a):Promise.reject()).then(function(){var o=b.textContent;b.textContent=\'Copied!\';setTimeout(function(){b.textContent=o;},1500);}).catch(function(){try{var t=document.createElement(\'textarea\');t.value=a;document.body.appendChild(t);t.select();document.execCommand(\'copy\');t.remove();var o=b.textContent;b.textContent=\'Copied!\';setTimeout(function(){b.textContent=o;},1500);}catch(e){}});})(this)" style="background:#633806;color:#FAC775;font-family:\'Space Mono\',monospace;font-size:8px;letter-spacing:0.12em;text-transform:uppercase;border:none;padding:5px 12px;cursor:pointer;margin-bottom:10px;display:inline-flex;align-items:center;gap:5px;"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="11" height="11" rx="1"/><path d="M5 15V5a1 1 0 0 1 1-1h10"/></svg> Copy</button>')

TEST_FILES = [
    "grindorium-burnout.html",
    "grindorium-anxiety.html",
    "grindorium-procrastination.html",
    "grindorium-numbness.html",
    "grindorium-attachment.html",
    "grindorium-selfesteem.html",
    "grindorium-perfectionism.html",
    "grindorium-stress.html",
    "grindorium-peoplepleasing.html",
    "grindorium-loneliness.html",
    "grindorium-selfsabotage.html",
    "grindorium-discipline.html",
    "grindorium-emotionalmaturity.html",
]


def process_file(filepath, dry_run=False):
    text = filepath.read_text(encoding="utf-8")

    if ADDR_BOX not in text:
        return "SKIP_NO_ADDR_BOX"

    if "Copy</button>" in text:
        return "SKIP_ALREADY_HAS_BTN"

    new_text = text.replace(ADDR_BOX, ADDR_BOX_WITH_BTN, 1)

    if text == new_text:
        return "SKIP_NO_CHANGE"

    if dry_run:
        return "DRY_RUN_OK"

    filepath.write_text(new_text, encoding="utf-8")
    return "OK"


def main():
    dry_run = "--dry-run" in sys.argv
    only = None
    if "--only" in sys.argv:
        idx = sys.argv.index("--only")
        only = sys.argv[idx + 1]

    files = [REPO_ROOT / f for f in TEST_FILES]
    if only:
        files = [f for f in files if f.name == only]

    updated = 0
    skipped = 0
    for f in files:
        result = process_file(f, dry_run=dry_run)
        print(f"  {f.name}: {result}")
        if result == "OK":
            updated += 1
        else:
            skipped += 1

    print(f"\nToplam: {updated} guncellendi, {skipped} atlandi")


if __name__ == "__main__":
    main()
