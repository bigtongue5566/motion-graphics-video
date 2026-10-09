"""Original wafer and semiconductor concepts, with on-screen source references."""
import argparse
import math
from pathlib import Path
import sys

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("mode",choices=["preview","render"])
parser.add_argument("--project",type=Path,required=True)
args=parser.parse_args()
sys.path.insert(0,str(args.project.resolve()/"work"))
import numpy as np
from PIL import Image
import skia
from original_renderer import Film,ease,paint,color


class SiliconFilm(Film):
    def background(self,light):
        surface=skia.Surface(self.w,self.h)
        c=surface.getCanvas()
        c.clear(color("#F3F0E9" if light else "#10151B"))
        line="#14202A" if light else "#D7E6E9"
        for x in range(96,1840,64):
            for y in range(140,900,64):
                c.drawCircle(x,y,1.2,paint(line,.07 if light else .055))
        return surface.makeImageSnapshot()

    def line(self,c,x1,y1,x2,y2,fg,alpha=.4,width=2):
        c.drawLine(x1,y1,x2,y2,paint(fg,alpha,width))

    def box(self,c,x,y,w,h,fg,alpha=.3,fill=False):
        c.drawRoundRect(skia.Rect.MakeXYWH(x,y,w,h),5,5,paint(fg,alpha,None if fill else 2))

    def wafer(self,c,t,level,fg,accent,cx=1400,cy=540,r=330,tilt=.72):
        c.save();c.translate(cx,cy);c.scale(1,tilt);c.rotate(-9+math.sin(t*.12)*5)
        c.drawCircle(0,8,r+6,paint(fg,.12))
        c.drawCircle(0,0,r,paint(fg,.045))
        c.drawCircle(0,0,r,paint(fg,.7,2))
        c.drawCircle(0,0,r+12,paint(accent,.06+self.pulse_at(t)*.30,1.5))
        c.save();c.clipPath(skia.Path.Circle(0,0,r-7))
        spacing=49
        for row in range(-7,8):
            for col in range(-7,8):
                x,y=col*spacing,row*spacing
                energy=.15+.85*(.5+.5*math.sin(col*.78+row*.5-t*1.5))
                if x*x+y*y<(r+15)**2:
                    self.box(c,x-20,y-20,40,40,accent,.08+energy*.22,True)
                    self.box(c,x-20,y-20,40,40,fg,.24+energy*.35)
                    self.line(c,x-10,y,x+10,y,accent,.45+level*.4,1.4)
        sweep=(t*.21%1)*r*2-r
        c.drawRect(skia.Rect.MakeXYWH(sweep-16,-r,32,r*2),paint(accent,.20))
        c.restore()
        for i in range(48):
            angle=i*math.tau/48
            rr=r+17
            self.line(c,math.cos(angle)*rr,math.sin(angle)*rr,math.cos(angle)*(rr+8),math.sin(angle)*(rr+8),fg,.30,1)
        c.restore()
        self.text(c,"WAFER / ORIGINAL CONCEPT",cx,cy+int(r*tilt)+72,21,fg,.55,center=True)

    def packets(self,c,points,t,accent,n=7):
        segments=[math.dist(a,b) for a,b in zip(points,points[1:])]
        total=sum(segments)
        for i in range(n):
            distance=((t*.18+i/n)%1)*total
            for a,b,length in zip(points,points[1:],segments):
                if distance<=length:
                    u=distance/length
                    x,y=a[0]+(b[0]-a[0])*u,a[1]+(b[1]-a[1])*u
                    c.drawCircle(x,y,4.5+self.pulse_at(t)*2.5,paint(accent,.85));break
                distance-=length

    def foundry(self,c,t,u,fg,accent):
        nodes=[(1090,285,"客戶設計"),(1410,515,"晶圓製造"),(1680,745,"終端應用")]
        points=[(x,y) for x,y,label in nodes]
        self.path(c,points,fg,.28,2)
        self.packets(c,points,t,accent)
        for i,(x,y,label) in enumerate(nodes):
            alpha=ease((u-i*.45)/.8)
            self.box(c,x-106,y-78,212,156,fg,alpha*.6)
            self.box(c,x-106,y-78,212,156,accent,alpha*.045,True)
            self.text(c,label,x,y+116,30,fg,alpha,center=True)
            for row in range(5):
                for col in range(7):
                    xx,yy=x-70+col*23,y-44+row*22
                    energy=.3+.7*math.sin(t+row*.9+col)**2
                    if i==0:
                        self.line(c,xx,yy,xx+14,yy,accent,energy*alpha,2)
                        if col%2:self.line(c,xx,yy,xx,yy+14,fg,.28*alpha,1)
                    elif i==1:
                        c.drawCircle(xx,yy,4,paint(accent,energy*alpha))
                    else:
                        self.box(c,xx-5,yy-5,11,11,accent,energy*alpha)
        self.text(c,"概念流程 / 非實際生產線",1410,919,22,fg,.55,center=True)

    def slab(self,c,cx,cy,w,h,depth,fg,accent,alpha=1):
        points=[(cx,cy-h),(cx+w,cy),(cx,cy+h),(cx-w,cy)]
        self.path(c,[(cx-w,cy),(cx,cy+h),(cx+w,cy),(cx+w,cy+depth),(cx,cy+h+depth),(cx-w,cy+depth)],fg,.10*alpha,closed=True,fill=True)
        self.path(c,points,accent,.11*alpha,closed=True,fill=True)
        self.path(c,points,fg,.72*alpha,2,True)
        for x,y in points[1:]:self.line(c,x,y,x,y+depth,fg,.35*alpha,1.3)
        self.path(c,[(cx-w,cy+depth),(cx,cy+h+depth),(cx+w,cy+depth)],fg,.35*alpha,1.3)

    def nanosheet(self,c,t,u,level,fg,accent):
        cx,cy=1405,510
        for j in range(3):
            y=cy-95+j*94
            self.slab(c,cx,y,285,58,17,fg,accent)
            points=[(cx-285,y),(cx,y+58),(cx+285,y)]
            self.packets(c,points,t+j*.7,accent,5)
        self.path(c,[(cx-70,cy-270),(cx+70,cy-240),(cx+70,cy+280),(cx-70,cy+250),(cx-70,cy-270)],accent,.75,5)
        self.text(c,"NANOSHEET",cx,850,38,fg,.8,center=True)
        self.text(c,"電晶體概念示意・非實際尺寸",cx,895,24,fg,.55,center=True)
        for i in range(15):
            xx=1080+i*47
            hh=14+float(self.spectra[min(len(self.spectra)-1,round(t*self.fps)),i])*28
            self.line(c,xx,938,xx,938-hh,accent,.4,2)

    def packaging(self,c,t,u,level,fg,accent):
        cx,cy=1400,655
        spread=1-ease(u/3)
        self.slab(c,cx,cy+115,344,105,22,fg,accent)
        self.slab(c,cx,cy-5-spread*72,316,94,18,fg,accent)
        y=cy-144-spread*155
        self.slab(c,cx,y,138,53,60,fg,accent)
        self.text(c,"運算",cx,y-13,29,fg,.8,center=True)
        for i,xx in enumerate([cx-248,cx+248]):
            for layer in range(4):
                yy=y+12-layer*16
                self.slab(c,xx,yy,85,34,13,fg,accent)
            self.text(c,"HBM",xx,y-80,25,fg,.85,center=True)
        for xx in [cx-232,cx+232]:
            points=[(xx,cy-45),(cx,cy+20)]
            self.path(c,points,accent,.45,2)
            self.packets(c,points,t,accent,4)
        self.text(c,"封裝整合概念 / 非實際產品結構",cx,898,24,fg,.58,center=True)

    def icon(self,c,kind,x,y,fg,accent,t):
        if kind=="高效能運算":
            for i in range(3):
                self.box(c,x-42,y-38+i*27,84,21,fg,.65)
                c.drawCircle(x+25,y-27+i*27,3,paint(accent,.65+.3*math.sin(t+i)**2))
        elif kind=="智慧型手機":
            self.box(c,x-26,y-45,52,90,fg,.75)
            self.line(c,x-17,y-27,x+17,y-27,accent,.8)
            c.drawCircle(x,y+30,3,paint(accent,.8))
        elif kind=="物聯網":
            c.drawCircle(x,y,22,paint(fg,.72,2))
            for r in [33,45]:
                c.drawArc(skia.Rect.MakeLTRB(x-r,y-r,x+r,y+r),220,100,False,paint(accent,.75,2))
            c.drawCircle(x,y,4,paint(accent,.85))
        elif kind=="車用電子":
            self.path(c,[(x-48,y+13),(x-40,y-9),(x-22,y-27),(x+20,y-27),(x+39,y-9),(x+47,y+13),(x-48,y+13)],fg,.8,2,True)
            for xx in [x-28,x+28]:c.drawCircle(xx,y+14,9,paint(accent,.9,2))
        else:
            self.box(c,x-45,y-31,90,56,fg,.7)
            self.line(c,x,y+25,x,y+38,fg,.7)
            self.line(c,x-20,y+38,x+20,y+38,accent,.7)

    def applications(self,c,t,u,level,fg,accent):
        cx,cy=1410,536
        self.box(c,cx-75,cy-75,150,150,accent,.8)
        self.box(c,cx-65,cy-65,130,130,fg,.12,True)
        self.text(c,"IC",cx,cy+18,55,fg,.9,center=True)
        names=["高效能運算","智慧型手機","物聯網","車用電子","消費性電子"]
        for i,name in enumerate(names):
            angle=-math.pi/2+i*math.tau/5
            x,y=cx+math.cos(angle)*300,cy+math.sin(angle)*263
            self.line(c,cx,cy,x,y,fg,.2,1.5)
            self.packets(c,[(cx,cy),(x,y)],t+i*.3,accent,3)
            c.drawCircle(x,y,69,paint(fg,.045))
            c.drawCircle(x,y,69,paint(fg,.25,1.5))
            self.icon(c,name,x,y,fg,accent,t)
            self.text(c,name,x,y+103,25,fg,.85,center=True)

    def chrome(self,c,scene,t,light):
        fg="#14202A" if light else self.palette["text"]
        accent=self.palette["accent"]
        index=self.scenes.index(scene)+1
        self.text(c,f"{index:02d} / 08   SILICON EXPLAINED",100,77,22,fg,.75)
        self.text(c,"獨立製作 / 90 秒資料解說",1450,77,21,fg,.65,width=365)
        self.line(c,100,110,1820,110,fg,.16,1)
        source_titles={"S1":"官方公司介紹","S2":"2025 年報","S3":"N2 技術頁","S4":"先進封裝技術頁"}
        refs="  ·  ".join(f"[{id}] {source_titles[id]}" for id in scene["sources"])
        self.text(c,refs,100,988,21,fg,.75,width=1210)
        self.text(c,self.cfg["editorial"]["notice"],1390,988,21,fg,.7,width=430)
        self.text(c,"資料查核 2026.10.10 / 來源網址見展示頁",100,1027,17,fg,.48)
        self.line(c,750,1021,1820,1021,fg,.15,2)
        self.line(c,750,1021,750+t/self.duration*1070,1021,accent,.9,3)

    def scene(self,c,scene,t,frame):
        kind=scene["kind"]
        light=kind in ("foundation","foundry","packaging","sources")
        c.drawImage(self.backgrounds[light],0,0)
        fg="#14202A" if light else self.palette["text"]
        accent=self.palette["accent"]
        level=float(self.levels[frame])
        u=t-scene["start"]
        alpha=ease(u/.65)
        self.chrome(c,scene,t,light)
        if kind=="scale":
            self.text(c,"2025 年",100,248,88,fg,alpha,bold=True)
            self.text(c,"服務的廣度",100,330,38,accent,alpha)
            items=[("305","種製程技術"),("534","個客戶"),("12,682","種不同產品")]
            for i,(value,label) in enumerate(items):
                cx=355+i*600
                for j in range(20):
                    xx=cx-165+(j%10)*37
                    yy=735+(j//10)*37
                    radius=4+float(self.spectra[frame,(i*10+j)%32])*8
                    c.drawCircle(xx,yy,radius,paint(accent,.4))
                self.text(c,value,cx,550,152,fg,ease((u-i*.32)/1.1),center=True,width=505,bold=True)
                self.text(c,label,cx,632,36,accent,alpha,center=True)
            self.text(c,"統計期間：2025 年 / 台積電年報所揭露數據",100,908,26,fg,.65)
            return
        if kind=="sources":
            self.text(c,"台積電｜從設計到矽晶",100,229,60,fg,alpha,bold=True)
            self.text(c,"非官方・獨立介紹",100,294,31,accent,alpha)
            rows=[("S1","公司沿革、代工模式與終端應用","tsmc.com / 公司介紹"),
                  ("S2","2025 年服務規模","investor.tsmc.com / 2025 Annual Report"),
                  ("S3","N2 量產進度與技術","tsmc.com / 2nm Technology"),
                  ("S4","先進封裝整合概念","3dfabric.tsmc.com / CoWoS")]
            for i,(ref,title,url) in enumerate(rows):
                y=407+i*93
                self.text(c,f"[{ref}]",100,y,29,accent,alpha)
                self.text(c,title,208,y,31,fg,alpha)
                self.text(c,url,1050,y,23,fg,.70*alpha,width=750)
                self.line(c,100,y+29,1820,y+29,fg,.11,1)
            self.text(c,"完整網址、逐段引用與授權記錄",100,838,27,fg,alpha)
            self.text(c,"bigtongue5566.github.io/?demo=tsmc-explained",100,890,32,accent,alpha,width=1460)
            return
        self.text(c,"90 秒認識晶圓代工" if kind=="opening" else scene["caption"],100,245,31,accent,alpha,width=805)
        size=179 if kind in ("foundation","nanosheet") else 118 if kind=="opening" else 91
        self.text(c,scene["headline"],100,421+(1-alpha)*20,size,fg,alpha,width=805,bold=True)
        if kind=="opening":
            self.text(c,"TSMC",106,585,60,fg,.68*alpha)
            self.text(c,"從設計到矽晶",100,693,43,accent,alpha)
        if kind=="nanosheet":
            self.text(c,"2025 Q4 開始量產",100,635,39,accent,alpha,width=795)
            self.text(c,"採用 nanosheet 電晶體技術",100,700,31,fg,.78*alpha,width=780)
        self.text(c,scene["body"],100,838,28,fg,.83*ease((u-.2)/.7),width=790)
        c.save();c.clipRect(skia.Rect.MakeXYWH(955,155,900,800))
        if kind=="opening":self.wafer(c,t,level,fg,accent)
        elif kind=="foundation":
            self.wafer(c,t,level,fg,accent,cy=590,r=300,tilt=.76)
            self.text(c,"專注客戶設計的晶片製造",1400,266,31,fg,.8*alpha,center=True)
            self.text(c,"PURE-PLAY FOUNDRY",1400,318,28,accent,.8*alpha,center=True)
        elif kind=="foundry":self.foundry(c,t,u,fg,accent)
        elif kind=="nanosheet":self.nanosheet(c,t,u,level,fg,accent)
        elif kind=="packaging":self.packaging(c,t,u,level,fg,accent)
        elif kind=="applications":self.applications(c,t,u,level,fg,accent)
        c.restore()

    def preview(self):
        out=self.root/"outputs"
        board=Image.new("RGB",(1920,1080),self.palette["background"])
        for i,scene in enumerate(self.scenes):
            t=scene["start"]+min(4,(scene["end"]-scene["start"])/2)
            pic=Image.fromarray(self.frame(round(t*self.fps))).convert("RGB")
            pic.save(self.root/"work"/f"preview-{i:02d}.jpg",quality=94)
            board.paste(pic.resize((640,360),Image.Resampling.LANCZOS),((i%3)*640,(i//3)*360))
        board.save(out/"tsmc-explained-storyboard.jpg",quality=95)
        Image.fromarray(self.frame(5*self.fps)).convert("RGB").save(out/"tsmc-explained-poster.jpg",quality=95)
        print("TSMC_STORYBOARD_READY",flush=True)


film=SiliconFilm(args.project)
getattr(film,args.mode)()
