"""
Adds compact Support card to test result screens.
Inserts before retake button, adds grndCopyAddr script after resultScreen close.
Run from repo root: python tools/add_support_card_tests.py [--dry-run] [--only filename]
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

CARD_HTML = """\
  <div style="max-width:440px;margin:36px auto 0;">
    <div style="background:#412402;border-bottom:2px solid #EF9F27;padding:14px 20px;text-align:center;display:flex;align-items:center;justify-content:center;gap:12px;">
      <div style="display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;background:#EF9F27;flex-shrink:0;">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#412402" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9h13v6a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V9z"/><path d="M16 10h2.2a2.3 2.3 0 0 1 0 4.6H16"/><path d="M6.5 5.5c0-1 .8-1 .8-2M10 5.5c0-1 .8-1 .8-2M13.5 5.5c0-1 .8-1 .8-2"/></svg>
      </div>
      <div style="font-family:'Cormorant Garamond',serif;font-size:18px;font-weight:300;color:#FAEEDA;">Support Grindorium</div>
    </div>
    <div style="background:#2C2C2A;padding:18px 20px;text-align:center;">
      <p style="font-family:'Cormorant Garamond',serif;font-size:14px;font-weight:300;color:#FAC775;line-height:1.6;margin-bottom:14px;">Everything free, always. Fuel it with a coffee.</p>
      <div style="display:flex;gap:6px;justify-content:center;margin-bottom:10px;flex-wrap:wrap;">
        <span style="background:#633806;color:#FAC775;font-family:'Space Mono',monospace;font-size:8px;letter-spacing:0.15em;text-transform:uppercase;padding:3px 8px;">ETH</span>
        <span style="background:#633806;color:#FAC775;font-family:'Space Mono',monospace;font-size:8px;letter-spacing:0.15em;text-transform:uppercase;padding:3px 8px;">USDT</span>
        <span style="background:#633806;color:#FAC775;font-family:'Space Mono',monospace;font-size:8px;letter-spacing:0.15em;text-transform:uppercase;padding:3px 8px;">USDC</span>
      </div>
      <div onclick="grndCopyAddr(this)" title="Click to copy" style="background:#444441;font-family:'Space Mono',monospace;font-size:9px;color:#FAEEDA;word-break:break-all;padding:10px 12px;cursor:pointer;margin-bottom:6px;text-align:left;border:1px solid rgba(250,238,218,0.08);">0x467eff5639e0db4d8b333df463facaa997bc8aac</div>
      <p style="font-family:'Space Mono',monospace;font-size:8px;color:#888780;letter-spacing:0.06em;margin-bottom:14px;">Ethereum &middot; Base &middot; Optimism &middot; BNB Chain</p>
      <div style="display:inline-block;background:#EF9F27;color:#412402;font-family:'Space Mono',monospace;font-size:8px;letter-spacing:0.15em;text-transform:uppercase;padding:9px 20px;cursor:default;">Ko-fi &middot; coming soon</div>
    </div>
  </div>
"""

SCRIPT_LINE = '<script>if(!window.grndCopyAddr){window.grndCopyAddr=function(el){var a=el.textContent.trim();(navigator.clipboard?navigator.clipboard.writeText(a):Promise.reject()).then(function(){var o=el.textContent;el.textContent=\'Copied.\';setTimeout(function(){el.textContent=o;},1800);}).catch(function(){var t=document.createElement(\'textarea\');t.value=a;document.body.appendChild(t);t.select();document.execCommand(\'copy\');t.remove();var o=el.textContent;el.textContent=\'Copied.\';setTimeout(function(){el.textContent=o;},1800);});}}</script>'

RETAKE_BTN = '  <button class="retake-btn" onclick="retakeTest()">Take it again</button>\n</div>'

TEST_FILES = [
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

    if "grndCopyAddr" in text:
        return "SKIP_ALREADY_HAS_CARD"

    if RETAKE_BTN not in text:
        return "SKIP_NO_RETAKE_BTN"

    new_text = text.replace(
        RETAKE_BTN,
        CARD_HTML + RETAKE_BTN + "\n" + SCRIPT_LINE,
        1
    )

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
