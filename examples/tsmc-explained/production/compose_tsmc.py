"""An original, restrained electronic score for the sourced silicon explainer."""
import argparse
from pathlib import Path
import sys

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--project",type=Path,required=True)
args=parser.parse_args()
sys.path.insert(0,str(args.project.resolve()/"work"))
import instruments as ins
from compose_edm import Score
from projectlib import load


class SiliconScore(Score):
    def arrange(self):
        kick,clap,hat=ins.kick(),ins.clap(),ins.hat()
        for index,chord in enumerate(self.harmony):
            a,b,role=chord["start"],chord["end"],chord["role"]
            span=b-a
            active=role in ("groove","build","drop")
            drop=role=="drop"
            for pitch in chord["voices"]:
                length=span-.06
                self.note("pad",a,length,pitch+12,.09,sound=ins.pad_voice(pitch+12,length),boundary=b)
            # A rising answer and a descending answer follow the current chord.
            degrees=([0,1,2,1,0] if index%4<2 else [2,1,0,1,2])
            offsets=[0,.75,1.5,2.5,3.25]
            lengths=[.62,.46,.72,.45,.5]
            for j,(off,degree,beats) in enumerate(zip(offsets,degrees,lengths)):
                length=beats*self.beat
                pitch=chord["voices"][degree]+12
                stem="lead" if active else "keys"
                sound=ins.pluck(pitch,length,1750 if drop else 1350) if active else self.keys(pitch,length)
                gain=.33 if drop else .23 if active else .16
                self.note(stem,a+off*self.beat,length,pitch,gain,pan=.07 if j%2 else -.07,sound=sound,boundary=b)
            if not active:
                continue
            for beat in range(4):
                start=a+beat*self.beat
                self.add("drums",start,kick,.65 if drop else .43)
                self.kicks.append(start)
                self.events.append({"stem":"drums","time":start,"duration":.12,"note":36,"velocity":92})
                if beat%2:
                    self.add("drums",start,clap,.48 if drop else .32)
                    self.events.append({"stem":"drums","time":start,"duration":.1,"note":39,"velocity":75})
                self.add("drums",start+self.beat*.5,hat,.34,pan=.16 if beat%2 else -.16)
                self.events.append({"stem":"drums","time":start+self.beat*.5,"duration":.08,"note":42,"velocity":55})
                for off in ([.5,.875] if drop else [.5]):
                    length=self.beat*.26
                    self.note("bass",start+off*self.beat,length,chord["root"],.50,
                              sound=ins.bass_note(chord["root"],length),boundary=b)
                if drop:
                    for pitch in chord["voices"]:
                        length=self.beat*.4
                        self.note("chords",start+self.beat*.5,length,pitch+12,.105,
                                  sound=ins.chord_voice(pitch+12,length,False),boundary=b)
            if role=="build":
                for j in range(8):
                    length=self.beat*.2
                    pitch=chord["voices"][[0,1,2,1][j%4]]+24
                    self.note("arp",a+j*self.beat/2,length,pitch,.022,
                              pan=.2 if j%2 else -.2,sound=ins.pluck(pitch,length,1000),boundary=b)
        for section in self.cfg["sections"]:
            if section["role"]=="drop":
                self.add("effects",section["start"],ins.crash(),.20)
                self.add("effects",section["start"]-1.5,ins.swell(1.5),.36)
        self.instrument_source="Original silicon-themed electronic score; oscillator and noise synthesis; no third-party recordings"


root,cfg=load(args.project)
score=SiliconScore(root,cfg)
score.arrange()
score.audit()
score.mix()
score.write_midi(root/"outputs"/(cfg["slug"]+"-music.mid"))
print("SILICON_SCORE_COMPLETE",flush=True)
