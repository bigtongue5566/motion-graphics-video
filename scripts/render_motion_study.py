"""Original silent visual study: focal object, path hand-off, stagger and resolved ending.

Uses the existing starter's Skia drawing/font/FFmpeg pipeline, not a new engine.
Run with the starter dependencies: uv run --python <venv-python> python <this-file>
    --output <new-directory> [--preview-only] [--samples 3] [--cn-font path] [--en-font path]
This is a visual exercise, not a substitute for a finished, scored client film.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import imageio_ffmpeg
import numpy as np
from PIL import Image
from scipy.interpolate import PchipInterpolator
import skia

STARTER = Path(__file__).resolve().parents[1] / 'assets' / 'starter'
sys.path.insert(0, str(STARTER))
import drawing as d
from render_video import Renderer

CREAM, INK, CORAL, TEAL = '#F4EFDF', '#182B32', '#F65A3D', '#68C5B4'
CUES = {'drop': .45, 'anticipate': 2.25, 'first_wipe': 2.65,
        'path_start': 3.2, 'path_land': 5.65, 'second_wipe': 5.75,
        'pattern_start': 6.2, 'resolve': 8.55, 'end': 10.}


class Study(Renderer):
    def __init__(self, root, cfg, samples=3):
        super().__init__(root, cfg)
        self.samples = samples
        # Shape-preserving interpolation gives authored acceleration and settling.
        self.drop = PchipInterpolator([0,.30,.45,.56,.72,.92,2.25,2.45,2.65,3.2],
                                      [-210,265,500,466,506,500,500,526,500,500])
        self.squash = PchipInterpolator([0,.38,.45,.54,.72,.95,2.25,2.45,2.65,3.2],
                                        [1,.88,1.13,.96,1.02,1,1,1.08,1,1])
        self.path = skia.Path()
        self.path.moveTo(340,660)
        self.path.cubicTo(520,660,410,370,680,370)
        self.path.cubicTo(980,370,820,760,1110,760)
        self.path.cubicTo(1410,760,1240,460,1580,460)
        self.measure = skia.PathMeasure(self.path, False)
        self.travel = PchipInterpolator([3.2,3.55,4.2,4.6,5.1,5.65],
                                        [0,.035,.32,.52,.83,1])

    def route(self, progress):
        position, _ = self.measure.getPosTan(self.measure.getLength()*d.clamp(progress))
        return position.x(), position.y()

    def draw_geometry(self, t):
        c=self.surface.getCanvas(); c.clear(d.color(CREAM)); c.save()
        c.scale(self.width/1920, self.height/1080)
        if t<3.2:
            # Broad areas and quiet line accents frame a single large focal object.
            d.circle(c,1320,500,235,INK,.12,2)
            d.circle(c,1320,500,310,INK,.06,1)
            d.rect(c,1090,750,460,3,INK,.3)
            q=d.smooth((t-2.65)/.55)
            if q>0:d.circle(c,1320,500,2400*q,INK)
            x=d.lerp(1320,340,q);y=d.lerp(float(self.drop(min(t,3.2))),660,q)
            radius=d.lerp(165,31,q)
            sx=float(self.squash(min(t,3.2)));sy=1/sx
            c.save();c.translate(x,y);c.scale(sx,sy)
            d.circle(c,0,0,radius,CORAL);c.restore()
            if .45<=t<.85:
                p=(t-.45)/.4
                d.circle(c,1320,500,165+95*d.ease(p),CORAL,(1-p)*.3,4)
        elif t<6.2:
            c.clear(d.color(INK))
            p=float(self.travel(min(t,5.65)))
            d.line(c,[(130,835),(1790,835)],CREAM,1,.12)
            c.drawPath(self.path,d.paint(CREAM,.08,2))
            trail=skia.Path()
            self.measure.getSegment(0,self.measure.getLength()*p,trail,True)
            c.drawPath(trail,d.paint(TEAL,1,14))
            for k,z in enumerate([.0,.32,.52,.83,1.]):
                x,y=self.route(z)
                a=d.ease((p-z+.025)/.045)
                if a>0:
                    d.circle(c,x,y,11*a,CREAM)
                    d.circle(c,x,y,24*a,TEAL,.22,2)
            x,y=self.route(p)
            q=d.smooth((t-5.75)/.45)
            if q>0:d.circle(c,x,y,2400*q,CREAM)
            x=d.lerp(x,1118,q);y=d.lerp(y,350,q)
            d.circle(c,x,y,d.lerp(31,78,q),CORAL)
        else:
            # The arriving dot becomes one module; siblings answer in a diagonal wave.
            for row in range(3):
                for col in range(4):
                    x=1118+col*176;y=350+row*176
                    onset=6.2+(row+col)*.12
                    p=d.smooth((t-onset)/.60)
                    if row==col==0:p=1.
                    if p<=0:continue
                    offset=(1-p)*75
                    c.save();c.translate(x,y+offset);c.scale(p,p)
                    color=[CORAL,TEAL,INK,TEAL][(row+col)%4]
                    if (row+col)%3==0:
                        d.circle(c,0,0,78,color)
                    elif (row+col)%3==1:
                        d.rect(c,-78,-78,156,156,color,radius=22)
                        d.circle(c,0,0,32,CREAM)
                    else:
                        d.rect(c,-78,-78,156,156,color,radius=78)
                        d.rect(c,0,-78,78,156,CREAM)
                    c.restore()
            # A clean registration line resolves with the final typographic lock-up.
            p=d.smooth((t-7.75)/.8)
            d.rect(c,1040,910,684*p,5,INK)
        c.restore()

    def draw_type(self,t):
        c=self.surface.getCanvas();c.save();c.scale(self.width/1920,self.height/1080)
        dark=3.2<=t<5.95
        color=CREAM if dark else INK
        self.text(c,'MOTION STUDY  /  01',100,90,23,color,.65,cn=False)
        self.text(c,'POINT → PATH → PATTERN',1290,90,23,color,.65,cn=False)
        if t<2.65:
            a=d.ease((t-.12)/.38)
            c.save();c.clipRect(skia.Rect.MakeXYWH(90,265,850,460))
            self.text(c,'POINT',90,490+(1-a)*180,205,INK,cn=False)
            c.restore()
            self.text(c,'先建立焦點',105,600,43,INK,d.smooth((t-.65)/.3))
            self.text(c,'01 / 一個主體，一個明確落點',105,930,27,INK,.65)
        elif 3.2<=t<5.75:
            a=d.ease((t-3.2)/.35)
            self.text(c,'PATH',100,295,145,CREAM,a,cn=False)
            self.text(c,'讓動作，帶出下一幕',105,940,40,CREAM,a)
        elif t>=6.2:
            a=d.ease((t-6.2)/.6)
            c.save();c.clipRect(skia.Rect.MakeXYWH(90,270,850,440))
            self.text(c,'MAKE',100,460+(1-a)*210,172,INK,cn=False)
            self.text(c,'IT FLOW.',100,650+(1-a)*210,172,INK,cn=False,max_width=850)
            c.restore()
            self.text(c,'每個動作，都有去處。',110,770,40,INK,d.smooth((t-7.4)/.55))
            self.text(c,'03 / 從單一訊號，到完整構成',110,930,27,INK,d.smooth((t-7.8)/.5)*.65)
        c.restore()

    def render(self,t):
        # Geometry samples only. Keep typography crisp at the centre of the frame.
        phase=(0,3.2) if t<3.2 else (3.2,6.2) if t<6.2 else (6.2,10)
        if self.samples>1:
            buffers=[]
            for j in range(self.samples):
                at=t+.5/self.cfg['fps']*((j+.5)/self.samples-.5)
                at=float(np.clip(at,phase[0],phase[1]-1e-7))
                self.draw_geometry(at)
                buffers.append(np.asarray(self.surface.makeImageSnapshot()).astype(np.float32))
            pixels=np.rint(np.mean(buffers,axis=0)).astype(np.uint8)
            self.surface.getCanvas().drawImage(skia.Image.fromarray(pixels,colorType=skia.ColorType.kRGBA_8888_ColorType),0,0)
        else:self.draw_geometry(t)
        self.draw_type(t)
        return self.surface.makeImageSnapshot()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--preview-only',action='store_true')
    ap.add_argument('--samples',type=int,choices=[1,3,5],default=3)
    ap.add_argument('--cn-font',type=Path)
    ap.add_argument('--en-font',type=Path)
    args=ap.parse_args();root=args.output.resolve()
    if root.exists() and any(root.iterdir()):ap.error('Use an empty output directory to preserve earlier work')
    for folder in ['work','outputs','outputs/stills']:(root/folder).mkdir(parents=True,exist_ok=True)
    cfg=json.loads((STARTER/'project.json').read_text('utf-8'))
    cfg.update(name='Point / Path / Pattern',slug='motion-study',duration=10,fps=30,width=1920,height=1080)
    cfg['fonts']={'cn':str(args.cn_font.resolve()) if args.cn_font else None,
                  'en':str(args.en_font.resolve()) if args.en_font else None}
    cfg['scenes']=[dict(start=a,end=b,chapter=name,music_role='groove') for a,b,name in
                   [(0,3.2,'Point'),(3.2,6.2,'Path'),(6.2,10,'Pattern')]]
    (root/'project.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
    (root/'outputs/cues.json').write_text(json.dumps(CUES,indent=2),encoding='utf-8')
    film=Study(root,cfg,args.samples)
    times=[.45,1.4,2.9,3.7,4.6,5.9,6.8,7.5,9.2]
    fingerprints={}
    tiles=[]
    for t in times:
        dest=root/f'outputs/stills/{t:04.1f}.png';film.save(t,dest)
        fingerprints[t]=hashlib.sha256(film.render(t).tobytes()).hexdigest()
        tiles.append(Image.open(dest).convert('RGB').resize((640,360)))
    # Catch RGBA/BGRA conversion errors in the accumulation pass.
    sample=Image.open(root/'outputs/stills/01.4.png').convert('RGB')
    assert sample.getpixel((1320,500))==d.rgb(CORAL), 'Focal colour changed during compositing'
    assert sample.getpixel((900,900))==d.rgb(CREAM), 'Background colour changed during compositing'
    # Arbitrary seeking must not depend on previously rendered frames.
    for t in reversed(times):assert hashlib.sha256(film.render(t).tobytes()).hexdigest()==fingerprints[t]
    sheet=Image.new('RGB',(1920,1080),CREAM)
    for i,tile in enumerate(tiles):sheet.paste(tile,(i%3*640,i//3*360))
    sheet.save(root/'outputs/motion-study-contact-sheet.jpg',quality=94)
    # Inspect a fast passage with neighbouring frames, not only settled poses.
    strip=Image.new('RGB',(1920,540),CREAM)
    for i,frame in enumerate([10,12,14,16,18,20,22,24]):
        t=frame/30;dest=root/f'outputs/stills/drop-{frame:03}.png';film.save(t,dest)
        strip.paste(Image.open(dest).convert('RGB').resize((480,270)),(i%4*480,i//4*270))
    strip.save(root/'outputs/motion-study-filmstrip.jpg',quality=94)
    report={'silent_visual_study':True,'arbitrary_seek_deterministic':True,
            'compositing_colours_preserved':True,'motion_samples':args.samples}
    if not args.preview_only:
        film.film();dest=root/'outputs/motion-study.mp4';shutil.move(root/'work/picture.mp4',dest)
        ff=imageio_ffmpeg.get_ffmpeg_exe()
        p=subprocess.run([ff,'-v','error','-i',str(dest),'-progress','pipe:1','-f','null','-'],capture_output=True,check=True)
        assert not p.stderr and b'frame=300' in p.stdout
        reader=imageio_ffmpeg.read_frames(str(dest))
        metadata=next(reader);reader.close()
        assert metadata['size']==(1920,1080) and metadata['fps']==30 and abs(metadata['duration']-10)<.04
        report.update(duration=10,decoded_frames=300,width=1920,height=1080,fps=30)
    (root/'outputs/checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report),flush=True)


if __name__=='__main__':main()
