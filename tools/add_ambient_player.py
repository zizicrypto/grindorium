"""
Adds ambient music player (sound-btn icon + toggleAmbient + localStorage resume)
to writings/*.html article pages that don't already have it.
Run from repo root: python tools/add_ambient_player.py
Optional: --dry-run to preview, --only filename to process one file.
"""
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WRITINGS_DIR = REPO_ROOT / "writings"

PLAYER_BLOCK = """\
<style>
.sound-btn{position:fixed;bottom:80px;right:24px;width:40px;height:40px;border-radius:50%;border:1px solid rgba(126,184,232,0.25);background:rgba(7,11,18,0.95);display:flex;align-items:center;justify-content:center;cursor:pointer;z-index:200;transition:border-color 0.3s;}
.sound-btn:hover{border-color:rgba(126,184,232,0.6);}
.sound-icon{font-size:14px;color:#8aa0b8;transition:color 0.3s;}
.sound-btn::after{content:'';position:absolute;left:22%;top:50%;width:56%;height:1.5px;background:#8aa0b8;transform:rotate(-45deg);transition:opacity 0.3s;pointer-events:none;}
.sound-btn.sound-on::after{opacity:0;}
.sound-btn.sound-on{border-color:rgba(126,184,232,0.5);}
.sound-btn:hover .sound-icon{color:#7eb8e8;}
@media(max-width:768px){.sound-btn{bottom:70px;right:16px;width:36px;height:36px;}}
</style>
<div class="sound-btn" onclick="toggleAmbient()" title="Ambient sound"><span class="sound-icon" id="soundIcon">&#9834;</span></div>
<script>
(function(){
  var ambientCtx=null,ambientSrcNode=null,ambientGainNode=null,ambientBufCache=null,ambientOn=false;
  function toggleAmbient(){
    var sIcon=document.getElementById('soundIcon');
    if(ambientOn){
      if(ambientGainNode&&ambientCtx){ambientGainNode.gain.setTargetAtTime(0.0001,ambientCtx.currentTime,0.25);}
      setTimeout(function(){if(ambientSrcNode){try{ambientSrcNode.stop();}catch(e){}ambientSrcNode=null;}},700);
      ambientOn=false;
      if(sIcon)sIcon.style.color='#8aa0b8';
      var _sb=document.querySelector('.sound-btn');if(_sb)_sb.classList.remove('sound-on');
      try{localStorage.setItem('grnd_ambient','0');}catch(e){}
    } else {
      if(!ambientCtx)ambientCtx=new (window.AudioContext||window.webkitAudioContext)();
      if(ambientCtx.state==='suspended')ambientCtx.resume();
      var startSrc=function(){
        ambientSrcNode=ambientCtx.createBufferSource();
        ambientSrcNode.buffer=ambientBufCache;
        ambientSrcNode.loop=true;
        ambientSrcNode.loopStart=0.03;
        ambientSrcNode.loopEnd=ambientBufCache.duration-0.03;
        ambientGainNode=ambientCtx.createGain();
        ambientGainNode.gain.value=0.0001;
        ambientSrcNode.connect(ambientGainNode);
        ambientGainNode.connect(ambientCtx.destination);
        ambientSrcNode.start(0,0.03);
        ambientGainNode.gain.setTargetAtTime(0.16,ambientCtx.currentTime,1.2);
      };
      if(ambientBufCache){startSrc();}
      else{fetch('/sigmaeffect-cinematic-ambient-atmosphere-463222.mp3').then(function(r){return r.arrayBuffer();}).then(function(ab){return ambientCtx.decodeAudioData(ab);}).then(function(buf){ambientBufCache=buf;startSrc();}).catch(function(){});}
      ambientOn=true;
      if(sIcon)sIcon.style.color='#7eb8e8';
      var _sb2=document.querySelector('.sound-btn');if(_sb2)_sb2.classList.add('sound-on');
      try{localStorage.setItem('grnd_ambient','1');}catch(e){}
    }
  }
  window.toggleAmbient=toggleAmbient;
  try{
    if(localStorage.getItem('grnd_ambient')==='1'){
      var _sb=document.querySelector('.sound-btn');
      var _si=document.getElementById('soundIcon');
      if(_sb)_sb.classList.add('sound-on');
      if(_si)_si.style.color='#7eb8e8';
      function _once(){document.removeEventListener('click',_once,true);document.removeEventListener('scroll',_once,true);if(!ambientOn)toggleAmbient();}
      document.addEventListener('click',_once,true);
      document.addEventListener('scroll',_once,true);
    }
  }catch(e){}
})();
</script>
"""


def process_file(filepath, dry_run=False):
    text = filepath.read_text(encoding="utf-8")

    if 'toggleAmbient' in text:
        return "SKIP_ALREADY_HAS_PLAYER"

    if '</body>' not in text:
        return "SKIP_NO_BODY_TAG"

    new_text = text.replace('</body>', PLAYER_BLOCK + '</body>', 1)

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

    files = sorted(WRITINGS_DIR.glob("*.html"))
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
