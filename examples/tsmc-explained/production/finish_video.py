"""Mux and directly verify a finished original fixed-duration motion/music Demo."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

import imageio_ffmpeg
import numpy as np
from PIL import Image

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--project",type=Path,required=True)
args=parser.parse_args()
root=args.project.resolve()
cfg=json.loads((root/"project.json").read_text(encoding="utf-8"))
work,out=root/"work",root/"outputs"
ff=imageio_ffmpeg.get_ffmpeg_exe()
movie=out/(cfg["slug"]+f"-{cfg['duration']:g}s.mp4")


def run(arguments,log=None,binary=False):
    result=subprocess.run([ff,"-hide_banner",*arguments],capture_output=True,text=not binary,
                          encoding=None if binary else "utf-8",errors=None if binary else "replace",check=True)
    if log:(work/log).write_text(result.stdout+"\n"+result.stderr,encoding="utf-8")
    return result


run(["-y","-i",str(work/"picture.mp4"),"-i",str(out/(cfg["slug"]+".m4a")),"-map","0:v:0","-map","1:a:0","-c","copy",
     "-t",str(cfg["duration"]),"-movflags","+faststart","-metadata","title="+cfg["name"],
     "-metadata","comment=Original procedural animation and synthesized electronic music; see source and rights records.",str(movie)],"mux.log")
metadata=run(["-i",str(movie),"-map","0","-c","copy","-f","null","-"],"encoded-metadata.log")
duration=re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)",metadata.stderr)
seconds=int(duration[1])*3600+int(duration[2])*60+float(duration[3])
assert abs(seconds-cfg["duration"])<=.02
assert re.search(r"Video: h264[^\n]*1920x1080[^\n]*30 fps",metadata.stderr)
assert re.search(r"Audio: aac[^\n]*48000 Hz, stereo",metadata.stderr)
decode=run(["-v","error","-nostats","-i",str(movie),"-map","0:v:0","-an","-progress","pipe:1","-f","null","-"],"video-full-decode.log")
frames=int(re.findall(r"frame=(\d+)",decode.stdout)[-1])
assert frames==round(cfg["duration"]*cfg["video"]["fps"]) and not decode.stderr.strip()
levels=run(["-nostats","-i",str(movie),"-vn","-af","ebur128=peak=true","-f","null","-"],"final-audio-meter.log")
summary=levels.stderr[levels.stderr.rfind("Summary:"):]
lufs=float(re.search(r"I:\s*([-\d.]+) LUFS",summary)[1])
peak=float(re.search(r"Peak:\s*([-\d.]+) dBFS",summary)[1])
assert abs(lufs-cfg["music"]["lufs"])<1.5 and peak<-.5
sound=run(["-v","error","-i",str(movie),"-map","0:a:0","-f","f32le","-ac","2","-ar","48000","pipe:1"],binary=True)
samples=np.frombuffer(sound.stdout,dtype="<f4").reshape(-1,2)
assert not sound.stderr and np.isfinite(samples).all() and np.abs(samples).max()<1
assert abs(len(samples)/48000-cfg["duration"])<1024/48000+.001
drops=[s for s in cfg["sections"] if s["role"]=="drop"]
drop_time=(drops[-1] if cfg["slug"]=="tsmc-explained" else drops[0])["start"]+2.2
times=[s["start"]+min(2.5,(s["end"]-s["start"])/2) for s in cfg["video"]["scenes"]]+[cfg["duration"]-.05,4,4.5,drop_time,drop_time+.5]
qc=work/"qc";qc.mkdir(exist_ok=True)
images={}
for i,t in enumerate(times):
    target=qc/f"frame-{i:02d}.jpg"
    run(["-y","-v","error","-ss",str(t),"-i",str(movie),"-frames:v","1","-q:v","2",str(target)])
    image=Image.open(target).convert("RGB")
    assert image.size==(1920,1080)
    images[t]=image.copy()
board=Image.new("RGB",(1920,1080),cfg["video"]["palette"].get("background", "#080C16"))
for i,t in enumerate(times[:len(cfg["video"]["scenes"])]):
    board.paste(images[t].resize((640,360),Image.Resampling.LANCZOS),((i%3)*640,(i//3)*360))
board.save(out/(cfg["slug"]+"-encoded-storyboard.jpg"),quality=94)
changes={}
for a,b,label in [(4,4.5,"intro_motion"),(drop_time,drop_time+.5,"drop_motion")]:
    aa=np.asarray(images[a].crop((960,150,1800,900)).resize((420,375)),dtype=float)
    bb=np.asarray(images[b].crop((960,150,1800,900)).resize((420,375)),dtype=float)
    diff=float(np.abs(aa-bb).mean())
    assert diff>.3,(label,diff)
    changes[label]=round(diff,3)
report={"status":"FINAL_MP4_VERIFIED","file":movie.name,"duration_seconds":seconds,"width":1920,"height":1080,"fps":30,
        "fully_decoded_video_frames":frames,"audio_sample_rate":48000,"audio_channels":2,"audio_decoded_seconds":round(len(samples)/48000,5),
        "integrated_lufs":lufs,"true_peak_dbtp":peak,"full_decode_errors":0,"sampled_encoded_frames":len(times),
        "geometry_motion_difference":changes,"music_bpm":cfg["music"]["bpm"],"music_key":cfg["music"]["key"],
        "mp4_bytes":movie.stat().st_size,"mp4_sha256":hashlib.sha256(movie.read_bytes()).hexdigest(),
        "limits":"Objective verification does not certify subjective listening quality."}
(out/(cfg["slug"]+"-video-qc.json")).write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
