#!/usr/bin/env python3
import json, os
HERE=os.path.dirname(os.path.abspath(__file__))
b=json.load(open(os.path.join(HERE,"assets_b64.json")))
L=json.load(open(os.path.join(HERE,"layout.json")))
OUT="/Users/vadimmakarov/Documents/work-home/experiments/mi-band-9/AnalogFull/simulator.html"
CX,CY=L["center"]
wd=L["widgets"]["weekday"]; day=L["widgets"]["day"]
ba=L["widgets"]["battery"]; st=L["widgets"]["steps"]
RU=L["ru_wd"]

html=f"""<title>Mi Band 9 — Analog Full · Simulator</title>
<style>
  body {{ margin:0; min-height:100vh; background:#0d0d10; color:#e7e7ea;
    font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
    display:flex; flex-direction:column; align-items:center; gap:20px; padding:32px 16px 56px; box-sizing:border-box; }}
  h1 {{ font-size:18px; font-weight:600; margin:0; }}
  .sub {{ color:#8a8a92; font-size:12.5px; margin:-12px 0 0; }}
  .band {{ padding:14px; border-radius:38px; background:linear-gradient(155deg,#2a2a30,#141417);
    box-shadow:0 22px 60px rgba(0,0,0,.6), inset 0 0 0 1px #3a3a42; }}
  .screen {{ width:calc({L['screen']['w']}px*1.7); height:calc({L['screen']['h']}px*1.7);
    border-radius:26px; overflow:hidden; background:#000; }}
  canvas {{ width:100%; height:100%; display:block; }}
  .digi {{ font-variant-numeric:tabular-nums; font-size:15px; color:#bfbfc6; }}
  .digi b {{ color:#fff; }}
  .row {{ display:flex; gap:10px; flex-wrap:wrap; justify-content:center; }}
  button {{ background:#1c1c22; color:#e7e7ea; border:1px solid #34343c; border-radius:10px;
    padding:8px 14px; font-size:13px; cursor:pointer; }}
  button:hover {{ background:#26262e; }}
  button.on {{ background:#2563eb; border-color:#2563eb; color:#fff; }}
  .meta {{ max-width:430px; text-align:center; color:#7d7d86; font-size:12px; }}
  .ok {{ color:#3ec46d; }}
</style>
<h1>Mi Band 9 · "Analog Full"</h1>
<p class="sub">192 × 490 · weekday &amp; date — live · battery/steps — sample</p>
<div class="band"><div class="screen"><canvas id="c" width="{L['screen']['w']}" height="{L['screen']['h']}"></canvas></div></div>
<div class="digi" id="digi">--:--:--</div>
<div class="row">
  <button id="live" class="on">● Real time</button>
  <button id="demo">Demo 10:09:36</button>
</div>
<p class="meta">1:1 render from the Mi&nbsp;Create project assets. <span class="ok">All numbers, the dial and both rows fit within 192×490</span>.
On-device battery/steps come from data sources (Battery=20, Steps=23), date from Day=11/Week=12.</p>
<script>
const CX={CX}, CY={CY}, RU={json.dumps(RU,ensure_ascii=False)};
const WD={json.dumps(wd)}, DAY={json.dumps(day)}, BA={json.dumps(ba)}, ST={json.dumps(st)};
const SRC={{bg:"{b['background.png']}",hour:"{b['hand_hour.png']}",min:"{b['hand_minute.png']}",
  sec:"{b['hand_second.png']}",cap:"{b['center_cap.png']}"}};
const img={{}}; let n=0,t=Object.keys(SRC).length;
for(const k in SRC){{const im=new Image();im.onload=()=>{{if(++n===t)draw();}};im.src=SRC[k];img[k]=im;}}
const cv=document.getElementById('c'),x=cv.getContext('2d'),digi=document.getElementById('digi');
let live=true, demo={{h:10,m:9,s:36}};
function hand(im,deg){{x.save();x.translate(CX,CY);x.rotate(deg*Math.PI/180);x.drawImage(im,-CX,-CY);x.restore();}}
function txt(s,W,fs,col,align){{x.fillStyle=col;x.font=fs+'px -apple-system,Helvetica,Arial,sans-serif';
  x.textBaseline='middle';
  if(align==='right'){{x.textAlign='right';x.fillText(s,W.x+W.w,W.y+W.h/2);}}
  else if(align==='center'){{x.textAlign='center';x.fillText(s,W.x+W.w/2,W.y+W.h/2);}}
  else{{x.textAlign='left';x.fillText(s,W.x,W.y+W.h/2);}}}}
function draw(){{
  let h,m,s,ms,d=new Date();
  if(live){{h=d.getHours();m=d.getMinutes();s=d.getSeconds();ms=d.getMilliseconds();}}
  else{{h=demo.h;m=demo.m;s=demo.s;ms=0;}}
  x.clearRect(0,0,cv.width,cv.height);
  x.drawImage(img.bg,0,0);
  // live date (weekday + day)
  const wi=d.getDay(); // 0=Sunday matches source 12
  txt(RU[wi],WD,24,'#d2d2d7','center');
  txt(String(d.getDate()),DAY,27,'#d2d2d7','center');
  // battery / steps (sample values; device uses data sources)
  txt('84',BA,23,'#ffffff','right');
  txt('8432',ST,23,'#ffffff','left');
  // hands + cap
  hand(img.hour,(h%12)*30+m*0.5); hand(img.min,m*6+s*0.1); hand(img.sec,(s+ms/1000)*6);
  x.drawImage(img.cap,0,0);
  const p=v=>String(v).padStart(2,'0');
  digi.innerHTML=`<b>${{p(h)}}:${{p(m)}}:${{p(s)}}</b>`;
  requestAnimationFrame(draw);
}}
const bL=document.getElementById('live'),bD=document.getElementById('demo');
bL.onclick=()=>{{live=true;bL.classList.add('on');bD.classList.remove('on');}};
bD.onclick=()=>{{live=false;bD.classList.add('on');bL.classList.remove('on');}};
</script>
"""
open(OUT,"w").write(html); print("wrote",OUT,len(html))
