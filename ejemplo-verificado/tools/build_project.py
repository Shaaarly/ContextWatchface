#!/usr/bin/env python3
"""Build AnalogFull.fprj (DeviceType 366 = Mi Band 9) from layout.json."""
import json, os
HERE=os.path.dirname(os.path.abspath(__file__))
PROJ="/Users/vadimmakarov/Documents/work-home/experiments/mi-band-9/AnalogFull"
L=json.load(open(os.path.join(HERE,"layout.json")))
ALIGN={"Left":0,"Center":1,"Right":2}

def attrs(**kw): return " ".join(f'{k}="{v}"' for k,v in kw.items())

def imagelist(bitmaps):  # Shape=31 needs explicit (N): prefixes or the compiler crashes
    return "|".join(f"({i}):{b}" for i,b in enumerate(bitmaps))

w=[]
# static background (dial + ticks + clock numbers; stat row now empty)
w.append('<Widget '+attrs(Shape=30,Name="bg",Bitmap="background.png",X=0,Y=0,Width=192,Height=490,Alpha=255,Visible_Src=0)+'/>')
# weekday (imagelist, Index = Week source)
wd=L["widgets"]["weekday"]
w.append('<Widget '+attrs(Shape=31,Name="weekday",BitmapList=imagelist(wd["bitmaps"]),
    X=wd["x"],Y=wd["y"],Width=wd["w"],Height=wd["h"],Alpha=255,Alignment=1,
    DefaultIndex=0,Index_Src=wd["src"],Spacing=0,Blanking=0,Visible_Src=0)+'/>')
# day (num widget, Value = Day source)
g=L["widgets"]["day"]
w.append('<Widget '+attrs(Shape=32,Name="day",BitmapList="|".join(g["bitmaps"]),
    X=g["x"],Y=g["y"],Width=g["w"],Height=g["h"],Alpha=255,Visible_Src=0,
    Digits=g["digits"],Alignment=ALIGN[g["align"]],Value_Src=g["src"],
    Spacing=0,Blanking=1)+'/>')
# battery % (imagelist of pre-coloured "NN%" frames, Index = Battery percent source)
b=L["widgets"]["battery"]
w.append('<Widget '+attrs(Shape=31,Name="battery",BitmapList=imagelist(b["bitmaps"]),
    X=b["x"],Y=b["y"],Width=b["w"],Height=b["h"],Alpha=255,Alignment=1,
    DefaultIndex=b.get("default",100),Index_Src=b["src"],Spacing=0,Blanking=0,Visible_Src=0)+'/>')
# analog clock (hands rotate about 96,245) — above text so hands sweep over nothing important
w.append('<Widget '+attrs(Shape=27,Name="analog_clock",X=0,Y=0,Width=192,Height=490,Alpha=255,Visible_Src=0,
    HourHandCorrection_En=1,MinuteHandCorrection_En=1,Background_ImageName="clock_bg.png",
    BgImage_rotate_xc=96,BgImage_rotate_yc=245,HourHand_ImageName="hand_hour.png",
    HourImage_rotate_xc=96,HourImage_rotate_yc=245,MinuteHand_Image="hand_minute.png",
    MinuteImage_rotate_xc=96,MinuteImage_rotate_yc=245,SecondHand_Image="hand_second.png",
    SecondImage_rotate_xc=96,SecondImage_rotate_yc=245)+'/>')
# center cap on top of hands
w.append('<Widget '+attrs(Shape=30,Name="center_cap",Bitmap="center_cap.png",X=0,Y=0,Width=192,Height=490,Alpha=255,Visible_Src=0)+'/>')

xml='<?xml version="1.0" encoding="UTF-8"?>\n<FaceProject DeviceType="366" Id="167210065">\n    <Screen Title="Analog Full" Bitmap="preview.png">\n'
xml+="".join("        "+x+"\n" for x in w)
xml+='    </Screen>\n</FaceProject>\n'
open(os.path.join(PROJ,"AnalogFull.fprj"),"w").write(xml)
print("wrote AnalogFull.fprj  (",len(w),"widgets )")
print(xml)
