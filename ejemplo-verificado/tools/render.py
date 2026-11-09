#!/usr/bin/env python3
"""
Mi Band 9 analog watch face renderer  (192x490, 1.62" AMOLED).
Minimalist analog dial + live date (top) + battery%/steps on one line (bottom).
Static art (dial, ticks, clock numbers, icons, '%') is baked into background.png.
Dynamic values (weekday, day, battery, steps) are separate Mi Create widgets;
this script also generates their digit/weekday image assets and a layout.json
so the .fprj builder places them at the same coordinates shown in the preview.
"""
import math, os, sys, json, base64, datetime
from PIL import Image, ImageDraw, ImageFont

W, H = 192, 490
SS = 4
CX, CY = 96, 245
R = 96
R_NUM = 77                          # clock-number ring, pushed out slightly (was 78; capped so the +15% 3/9 still fit 192px)
R_TICK_OUT = 98                    # was 94: ticks pushed ~2mm (~25px) further out (may run off the edges — OK)
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
ASSETS = os.path.join(OUT, "images")   # write straight into the live images/ dir the simulator + compiler read
os.makedirs(ASSETS, exist_ok=True)

HOUR, MIN, SEC = 10, 9, 36
WHITE = (255,255,255,255)
DIM   = (210,210,215,255)
DIM2  = (160,160,166,255)
RED   = (255,45,45,255)
YELLOW= (255,205,40,255)
CARDINAL = {12,3,6,9}

def batt_color(v):                  # battery%: red <=5, yellow <=15, white otherwise
    if v <= 5:  return RED
    if v <= 15: return YELLOW
    return WHITE

# ---- data-source ids (Mi Band 9 table = xiaomi_band_9 in sources.json; NOT the
# generic xiaomi_color ids 11/12/20 — those read as 0 on Band 9 hardware) ----
SRC_DAY, SRC_WEEK, SRC_BATT = "1812", "2012", "0841"   # Day / Week / Battery percent

# ---- layout (1x px) — date/weekday/battery typography doubled (2x) ----
DATE_Y = 30; DATE_H = 60                       # pushed up toward the top edge, well clear of the dial
WD_W = 68                                      # weekday image box (2x of 34)
DAY_CELL = 34; DAY_W = DAY_CELL*2              # date digit cell (2x of 17)
DATE_GAP = 12
WD_X = CX - (WD_W+DATE_GAP+DAY_W)//2           # centre the date row on the dial axis
DAY_X = WD_X+WD_W+DATE_GAP
STAT_Y = 420; STAT_H = 60                      # battery row, pushed down toward the bottom edge
ST_CELL = 28                                   # legacy stat digit cell (2x of 14)
BATT_FRAME_W = 112                             # battery "NN%" frame, fits up to "100%"
BATT_X = CX - BATT_FRAME_W//2                  # centred on the dial axis

RU_WD = ["ВС","ПН","ВТ","СР","ЧТ","ПТ","СБ"]   # index = source 12 (0=Sunday)

# ---- typography & hand geometry: ONE source of truth shared by the main face
# AND the AOD variant. Tune here and BOTH faces follow. ----
NUM_FS, NUM_FB = 30, 44                 # clock numbers: non-cardinal / cardinal (12,3,6,9)
WD_FS, DAY_FS  = 48, 54                 # weekday word / date digits
BATT_FS        = 46                     # battery "NN%"
HOUR_LEN, MIN_LEN, SEC_LEN = 48, 72, 82 # hand lengths (widths/colours/tail are per-variant)

# ---- render variants. MAIN (display) and AOD differ ONLY in palette, dial
# density, hands and complications — every size/position/radius above is shared.
# hand spec = (colour,width,tail) or None to omit; cap = (r0,col0,r1,col1). ----
MAIN = {
    "dial":"full",                                                   # all 60 ticks + numbers 1..12
    "num":WHITE, "tick":(190,40,40,255), "tick_h":RED, "date":DIM,
    "hour":(WHITE,9,13), "minute":(WHITE,6,15), "second":(RED,3,22),
    "cap":(8,WHITE,3,RED),
}
AOD = {
    "dial":"sparse",                                                 # hour ticks only + cardinal numbers only
    "num":(150,150,155,255), "tick":(95,95,100,255), "tick_h":(95,95,100,255), "date":(110,110,115,255),
    "hour":((180,180,185,255),8,13), "minute":((180,180,185,255),5,15), "second":None,
    "cap":(6,(180,180,185,255),0,None),
}

def font(size):
    for path in ["/System/Library/Fonts/HelveticaNeue.ttc",
                 "/System/Library/Fonts/Helvetica.ttc",
                 "/Library/Fonts/Arial.ttf",
                 "/System/Library/Fonts/Supplemental/Arial.ttf"]:
        if os.path.exists(path):
            try: return ImageFont.truetype(path, size)
            except Exception: continue
    return ImageFont.load_default()

def canvas(): return Image.new("RGBA",(W*SS,H*SS),(0,0,0,0))
def save(img,name):
    img.resize((W,H),Image.LANCZOS).save(os.path.join(ASSETS,name)); return img

# ---------------- dial: ticks + clock numbers (shared by both variants) -------
# `v` is a variant dict (MAIN / AOD). "full" draws all 60 ticks + numbers 1..12;
# "sparse" (AOD) draws hour ticks + cardinal numbers only. Sizes/radii are global
# (NUM_FS/NUM_FB, R_NUM, R_TICK_OUT) so both faces stay in lockstep.
def build_dial(v):
    img = Image.new("RGBA",(W*SS,H*SS),(0,0,0,255))
    d = ImageDraw.Draw(img)
    cx,cy = CX*SS, CY*SS
    sparse = v["dial"]=="sparse"
    for m in range(60):
        is_h=(m%5==0)
        if sparse and not is_h: continue
        ang=math.radians(m*6-90); r_out=R_TICK_OUT*SS
        if sparse:
            r_in=(R_TICK_OUT-9)*SS; w=3*SS; col=v["tick_h"]
        else:
            r_in=(R_TICK_OUT-10)*SS if is_h else (R_TICK_OUT-5)*SS
            w=4*SS if is_h else 2*SS; col=v["tick_h"] if is_h else v["tick"]
        d.line([cx+r_out*math.cos(ang),cy+r_out*math.sin(ang),
                cx+r_in*math.cos(ang), cy+r_in*math.sin(ang)],fill=col,width=w)
    fs=font(NUM_FS*SS); fb=font(NUM_FB*SS); fit=[]
    for n in range(1,13):
        if sparse and n not in CARDINAL: continue
        f=fb if n in CARDINAL else fs
        ang=math.radians(n*30-90)
        nx=cx+R_NUM*SS*math.cos(ang); ny=cy+R_NUM*SS*math.sin(ang)
        bb=d.textbbox((0,0),str(n),font=f); tw,th=bb[2]-bb[0],bb[3]-bb[1]
        d.text((nx-tw/2-bb[0],ny-th/2-bb[1]),str(n),font=f,fill=v["num"])
        fit.append((n,(nx-tw/2)/SS,(nx+tw/2)/SS,(ny-th/2)/SS,(ny+th/2)/SS))
    # stat row carries no static art: '%' is baked into each coloured b_*.png frame.
    return img, fit

# ---------------- hands ----------------
def hand_image(length,width,color,tail=0):
    img=canvas(); d=ImageDraw.Draw(img); cx,cy=CX*SS,CY*SS
    L=length*SS; wd=width*SS; tl=tail*SS; r=wd/2
    d.line([cx,cy+tl,cx,cy-L],fill=color,width=int(wd))
    d.ellipse([cx-r,cy-L-r,cx+r,cy-L+r],fill=color)
    if tl>0: d.ellipse([cx-r,cy+tl-r,cx+r,cy+tl+r],fill=color)
    return img
def rot(img,deg): return img.rotate(-deg,resample=Image.BICUBIC,center=(CX*SS,CY*SS))
def make_hands(v):  # {"hour","minute","second"} images; a None spec -> transparent (omitted)
    out={}
    for name,length in (("hour",HOUR_LEN),("minute",MIN_LEN),("second",SEC_LEN)):
        spec=v[name]
        out[name]=canvas() if spec is None else hand_image(length,spec[1],spec[0],spec[2])
    return out
def make_cap(v):
    cap=canvas(); dc=ImageDraw.Draw(cap); cx,cy=CX*SS,CY*SS
    r0,c0,r1,c1=v["cap"]
    dc.ellipse([cx-r0*SS,cy-r0*SS,cx+r0*SS,cy+r0*SS],fill=c0)
    if r1>0: dc.ellipse([cx-r1*SS,cy-r1*SS,cx+r1*SS,cy+r1*SS],fill=c1)
    return cap

# ---------------- digit / weekday assets ----------------
def tile(text, cellw, cellh, fsize, color=WHITE):
    s=SS; im=Image.new("RGBA",(cellw*s,cellh*s),(0,0,0,0)); d=ImageDraw.Draw(im)
    f=font(fsize*s); bb=d.textbbox((0,0),text,font=f); tw,th=bb[2]-bb[0],bb[3]-bb[1]
    d.text(((cellw*s-tw)/2-bb[0],(cellh*s-th)/2-bb[1]),text,font=f,fill=color)
    return im.resize((cellw,cellh),Image.LANCZOS)
def batt_frame(v):
    # one full "NN%" image, centred in the frame, coloured by battery level (2x font)
    s=SS; im=Image.new("RGBA",(BATT_FRAME_W*s,STAT_H*s),(0,0,0,0)); d=ImageDraw.Draw(im)
    f=font(BATT_FS*s); txt=f"{v}%"; bb=d.textbbox((0,0),txt,font=f); tw,th=bb[2]-bb[0],bb[3]-bb[1]
    d.text(((BATT_FRAME_W*s-tw)/2-bb[0],(STAT_H*s-th)/2-bb[1]),txt,font=f,fill=batt_color(v))
    return im.resize((BATT_FRAME_W,STAT_H),Image.LANCZOS)
def gen_date_assets(v, outdir):                  # dd_*/wd_* in the variant's date colour, shared sizes
    for i in range(10):
        tile(str(i),DAY_CELL,DATE_H,DAY_FS,v["date"]).save(os.path.join(outdir,f"dd_{i}.png"))
    for i,w in enumerate(RU_WD):
        tile(w,WD_W,DATE_H,WD_FS,v["date"]).save(os.path.join(outdir,f"wd_{i}.png"))
def gen_battery_frames(outdir):                  # 101 coloured "NN%" frames (main face only)
    for v in range(101):
        batt_frame(v).save(os.path.join(outdir,f"b_{v}.png"))

# ---------------- helpers for preview text ----------------
def text_box(d,text,x,y,w,h,font_,fill,align="left"):
    cy=(y+h/2)*SS
    if align=="right":   d.text(((x+w)*SS,cy),text,font=font_,fill=fill,anchor="rm")
    elif align=="center":d.text(((x+w/2)*SS,cy),text,font=font_,fill=fill,anchor="mm")
    else:                d.text((x*SS,cy),text,font=font_,fill=fill,anchor="lm")

# ---------------- compose ----------------
def main():
    V=MAIN
    bg,fit = build_dial(V); save(bg,"background.png")
    save(canvas(),"clock_bg.png")
    hands=make_hands(V)
    save(hands["hour"],"hand_hour.png")
    save(hands["minute"],"hand_minute.png")
    save(hands["second"],"hand_second.png")
    cap=make_cap(V); save(cap,"center_cap.png")
    gen_date_assets(V,ASSETS); gen_battery_frames(ASSETS)

    # sample values for preview
    today=datetime.date.today()
    wd_idx=(today.weekday()+1)%7          # python Mon=0 -> source Sun=0
    day=today.day; batt=84

    comp=bg.copy()
    sa=SEC*6; ma=MIN*6+SEC*0.1; ha=(HOUR%12)*30+MIN*0.5
    comp.alpha_composite(rot(hands["hour"],ha))
    comp.alpha_composite(rot(hands["minute"],ma))
    comp.alpha_composite(rot(hands["second"],sa))
    comp.alpha_composite(cap)
    d=ImageDraw.Draw(comp)
    # date row (weekday + day)
    text_box(d,RU_WD[wd_idx],WD_X,DATE_Y,WD_W,DATE_H,font(WD_FS*SS),V["date"],"center")
    text_box(d,str(day),DAY_X,DATE_Y,DAY_W,DATE_H,font(DAY_FS*SS),V["date"],"center")
    # battery %, centred on the dial axis, coloured by level (steps removed)
    text_box(d,f"{batt}%",BATT_X,STAT_Y,BATT_FRAME_W,STAT_H,font(BATT_FS*SS),batt_color(batt),"center")

    prev=comp.resize((W,H),Image.LANCZOS).convert("RGB")
    prev.save(os.path.join(OUT,"preview.png"))
    prev.resize((W*3,H*3),Image.NEAREST).save(os.path.join(OUT,"preview_3x.png"))

    # ---- fit check ----
    ok=True; margin=999
    print(f"Canvas {W}x{H}  dial c=({CX},{CY}) R={R}  top={CY-R} bottom={CY+R}")
    for n,l,r,t,b in fit:
        ins=(l>=0 and r<=W and t>=0 and b<=H); margin=min(margin,l,W-r); ok&=ins
        print(f"  num {n:2d}: x[{l:6.1f},{r:6.1f}] {'OK' if ins else 'OFF'}")
    rows={"date row":(DATE_Y,DATE_Y+DATE_H,WD_X,DAY_X+DAY_W),
          "stat row":(STAT_Y,STAT_Y+STAT_H,BATT_X,BATT_X+BATT_FRAME_W)}
    for k,(y0,y1,x0,x1) in rows.items():
        fits = (y0>=0 and y1<=H and x0>=0 and x1<=W and (y0>CY+R or y1<CY-R or True))
        print(f"  {k}: x[{x0},{x1}] y[{y0},{y1}] {'OK' if x1<=W and x0>=0 else 'OFF'}")
        ok &= (x1<=W and x0>=0)
    print(f"min number margin {margin:.1f}px")
    print("ALL FIT" if ok else "WARNING: OFF-SCREEN")

    # ---- layout.json for the .fprj + simulator builders ----
    layout={
      "screen":{"w":W,"h":H},
      "widgets":{
        "weekday":{"shape":31,"x":WD_X,"y":DATE_Y,"w":WD_W,"h":DATE_H,"src":SRC_WEEK,
                   "bitmaps":[f"wd_{i}.png" for i in range(7)]},
        "day":{"shape":32,"x":DAY_X,"y":DATE_Y,"w":DAY_W,"h":DATE_H,"src":SRC_DAY,
               "digits":2,"align":"Center","bitmaps":[f"dd_{i}.png" for i in range(10)]},
        "battery":{"shape":31,"x":BATT_X,"y":STAT_Y,"w":BATT_FRAME_W,"h":STAT_H,"src":SRC_BATT,
                   "default":batt,"bitmaps":[f"b_{i}.png" for i in range(101)]},
      },
      "sample":{"wd":wd_idx,"day":day,"batt":batt},
      "ru_wd":RU_WD,
      "center":[CX,CY]
    }
    json.dump(layout,open(os.path.join(OUT,"layout.json"),"w"),ensure_ascii=False,indent=2)

    # ---- base64 for the live simulator ----
    b={}
    for nm in ["background.png","hand_hour.png","hand_minute.png","hand_second.png","center_cap.png"]:
        b[nm]="data:image/png;base64,"+base64.b64encode(open(os.path.join(ASSETS,nm),"rb").read()).decode()
    json.dump(b,open(os.path.join(OUT,"assets_b64.json"),"w"))
    print("layout.json + assets_b64.json written")

if __name__=="__main__": main()
