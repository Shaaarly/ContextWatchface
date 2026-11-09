#!/usr/bin/env python3
"""Build the low-power AOD variant: AnalogFull/AOD/{AOD.fprj, images/}.

AOD now shares ALL geometry, typography and positions with the main face via
render.py — it just renders the `render.AOD` variant instead of `render.MAIN`.
The only differences live in that one dict: dim palette, sparse dial (hour ticks
+ cardinal numbers), hour+minute hands (no second), no battery/steps. Change a
size/radius/position in render.py and BOTH faces follow."""
import sys, os, json, datetime, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R
from PIL import Image, ImageDraw

V = R.AOD
W,H,SS = R.W,R.H,R.SS
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = "/Users/vadimmakarov/Documents/work-home/experiments/mi-band-9/AnalogFull"
AOD  = os.path.join(PROJ,"AOD"); IMGDIR = os.path.join(AOD,"images")
MAIN_IMG = os.path.join(PROJ,"images")
os.makedirs(IMGDIR, exist_ok=True)

def save(img,name): img.resize((W,H),Image.LANCZOS).save(os.path.join(IMGDIR,name))

def main():
    bg,_ = R.build_dial(V); save(bg,"aod_bg.png")
    save(R.canvas(),"clock_bg.png")                 # transparent analog bg
    save(R.canvas(),"empty.png")                    # transparent => no second hand
    hands = R.make_hands(V)
    save(hands["hour"],"aod_hour.png")
    save(hands["minute"],"aod_minute.png")
    save(R.make_cap(V),"aod_cap.png")
    R.gen_date_assets(V, IMGDIR)                     # dim dd_/wd_, same sizes as the main face

    # ---- preview composite (hour+minute only, no second) ----
    today=datetime.date.today(); wd=(today.weekday()+1)%7; day=today.day
    comp=bg.copy()
    ha=(R.HOUR%12)*30+R.MIN*0.5; ma=R.MIN*6+R.SEC*0.1
    comp.alpha_composite(R.rot(hands["hour"],ha))
    comp.alpha_composite(R.rot(hands["minute"],ma))
    comp.alpha_composite(R.make_cap(V))
    d=ImageDraw.Draw(comp)
    R.text_box(d,R.RU_WD[wd],R.WD_X,R.DATE_Y,R.WD_W,R.DATE_H,R.font(R.WD_FS*SS),V["date"],"center")
    R.text_box(d,str(day),R.DAY_X,R.DATE_Y,R.DAY_W,R.DATE_H,R.font(R.DAY_FS*SS),V["date"],"center")
    prev=comp.resize((W,H),Image.LANCZOS).convert("RGB")
    prev.save(os.path.join(IMGDIR,"preview.png"))
    prev.resize((W*3,H*3),Image.NEAREST).save(os.path.join(HERE,"preview_aod_3x.png"))

    # ---- AOD.fprj (positions from tools/layout.json; sources from render.py) ----
    def a(**k): return " ".join(f'{x}="{v}"' for x,v in k.items())
    L=json.load(open(os.path.join(HERE,"layout.json")))
    dw=L["widgets"]["weekday"]; dy=L["widgets"]["day"]
    w=[]
    w.append('<Widget '+a(Shape=30,Name="bg",Bitmap="aod_bg.png",X=0,Y=0,Width=192,Height=490,Alpha=255,Visible_Src=0)+'/>')
    w.append('<Widget '+a(Shape=31,Name="weekday",BitmapList="|".join(f"({i}):wd_{i}.png" for i in range(7)),
        X=dw["x"],Y=dw["y"],Width=dw["w"],Height=dw["h"],Alpha=255,Alignment=1,DefaultIndex=0,Index_Src=R.SRC_WEEK,Spacing=0,Blanking=0,Visible_Src=0)+'/>')
    w.append('<Widget '+a(Shape=32,Name="day",BitmapList="|".join(f"dd_{i}.png" for i in range(10)),
        X=dy["x"],Y=dy["y"],Width=dy["w"],Height=dy["h"],Alpha=255,Visible_Src=0,Digits=2,Alignment=1,Value_Src=R.SRC_DAY,Spacing=0,Blanking=1)+'/>')
    w.append('<Widget '+a(Shape=27,Name="analog_clock",X=0,Y=0,Width=192,Height=490,Alpha=255,Visible_Src=0,
        HourHandCorrection_En=1,MinuteHandCorrection_En=1,Background_ImageName="clock_bg.png",
        BgImage_rotate_xc=96,BgImage_rotate_yc=245,HourHand_ImageName="aod_hour.png",HourImage_rotate_xc=96,HourImage_rotate_yc=245,
        MinuteHand_Image="aod_minute.png",MinuteImage_rotate_xc=96,MinuteImage_rotate_yc=245,
        SecondHand_Image="empty.png",SecondImage_rotate_xc=96,SecondImage_rotate_yc=245)+'/>')
    w.append('<Widget '+a(Shape=30,Name="center_cap",Bitmap="aod_cap.png",X=0,Y=0,Width=192,Height=490,Alpha=255,Visible_Src=0)+'/>')
    xml='<?xml version="1.0" encoding="UTF-8"?>\n<FaceProject DeviceType="366" Id="167210065">\n    <Screen Title="Analog Full AOD" Bitmap="preview.png">\n'
    xml+="".join("        "+x+"\n" for x in w)+'    </Screen>\n</FaceProject>\n'
    open(os.path.join(AOD,"AOD.fprj"),"w").write(xml)

    # The compiler resolves the AOD sub-face's images from the MAIN images/ dir
    # (not AOD/images/), so mirror the AOD-only assets there or the build fails
    # with "unable to open image .../images/empty.png".
    for f in ("aod_bg.png","aod_cap.png","aod_hour.png","aod_minute.png","empty.png"):
        shutil.copy(os.path.join(IMGDIR,f), os.path.join(MAIN_IMG,f))
    print("AOD built ->",AOD,"(+ aod_*/empty.png mirrored into images/)")

if __name__=="__main__": main()
