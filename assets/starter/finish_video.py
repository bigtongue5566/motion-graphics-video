"""Two-pass mastering, chapter mux, and direct encoded-media verification."""
import argparse
import json
from pathlib import Path
import re
import subprocess

import imageio_ffmpeg
import numpy as np
from PIL import Image

from projectlib import load


class Finisher:
    def __init__(self, root, cfg):
        self.root, self.cfg = root, cfg
        self.work, self.out = root / "work", root / "outputs"
        self.ff = imageio_ffmpeg.get_ffmpeg_exe()
        self.film = self.out / f"{cfg['slug']}.mp4"
        self.bgm = self.out / f"{cfg['slug']}-bgm.m4a"

    def run(self, args, log):
        p = subprocess.run([self.ff, "-hide_banner", "-nostats", *args], capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
        (self.work / log).write_text(p.stdout + "\n" + p.stderr, encoding="utf-8")
        if p.returncode:
            raise RuntimeError(p.stderr[-2000:])
        return p

    def master(self):
        music = self.cfg["music"]
        base = f"loudnorm=I={music['lufs']}:TP={music['true_peak']}:LRA=9"
        p = self.run(["-i", str(self.work / "score-mix.wav"), "-af", base + ":print_format=json",
                      "-f", "null", "-"], "loudness-analysis.log")
        values = json.loads(re.search(r'\{\s*"input_i".*?\}', p.stderr, re.S).group(0))
        filter_ = base + ":" + ":".join(f"{key}={values[value]}" for key, value in [
            ("measured_I", "input_i"), ("measured_TP", "input_tp"), ("measured_LRA", "input_lra"),
            ("measured_thresh", "input_thresh"), ("offset", "target_offset")]) + ":linear=true:print_format=json"
        self.run(["-y", "-i", str(self.work / "score-mix.wav"), "-af", filter_, "-ar", "48000",
                  "-c:a", "pcm_s24le", str(self.work / "score-master.wav")], "mastering.log")
        self.run(["-y", "-i", str(self.work / "score-master.wav"), "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
                  "-movflags", "+faststart", "-metadata", "title=" + self.cfg["name"] + " - Original EDM",
                  str(self.bgm)], "bgm-encoding.log")
        print("MUSIC_MASTERED", flush=True)

    def mux(self):
        def safe(value):
            value = str(value).replace("\n", " ").replace("\r", " ").replace("\\", "\\\\")
            for character in ["=", ";", "#"]:
                value = value.replace(character, "\\" + character)
            return value
        metadata = ";FFMETADATA1\ntitle=" + safe(self.cfg["name"]) + "\n"
        for scene in self.cfg["scenes"]:
            metadata += ("[CHAPTER]\nTIMEBASE=1/1000000\n" + f"START={round(scene['start'] * 1000000)}\n"
                         + f"END={round(scene['end'] * 1000000)}\n" + "title=" + safe(scene["chapter"]) + "\n")
        (self.work / "chapters.txt").write_text(metadata, encoding="utf-8")
        self.run(["-y", "-i", str(self.work / "picture.mp4"), "-i", str(self.bgm), "-i", str(self.work / "chapters.txt"),
                  "-map", "0:v:0", "-map", "1:a:0", "-map_metadata", "2", "-map_chapters", "2", "-c", "copy",
                  "-t", str(self.cfg["duration"]), "-movflags", "+faststart", str(self.film)], "mux.log")
        print("FILM_MUXED", flush=True)

    def verify(self):
        reader = imageio_ffmpeg.read_frames(str(self.film))
        try:
            metadata = next(reader)
        finally:
            reader.close()
        cfg = self.cfg
        if tuple(metadata["size"]) != (cfg["width"], cfg["height"]):
            raise ValueError("Encoded dimensions differ from the project")
        if abs(metadata["fps"] - cfg["fps"]) > .02:
            raise ValueError("Encoded frame rate differs from the project")
        if abs(metadata["duration"] - cfg["duration"]) > max(.04, 1 / cfg["fps"]):
            raise ValueError("Encoded duration differs from the requested duration")
        p = self.run(["-v", "error", "-i", str(self.film), "-map", "0:v:0", "-map", "0:a:0", "-progress", "pipe:1",
                      "-f", "null", "-"], "full-decode.log")
        frames = re.findall(r'^frame=(\d+)', p.stdout, re.M)
        if not frames or int(frames[-1]) != round(cfg["duration"] * cfg["fps"]) or p.stderr.strip():
            raise ValueError("Full-film decode/frame-count verification failed")
        p = self.run(["-i", str(self.film), "-map", "0:a:0", "-af", "ebur128=peak=true", "-f", "null", "-"], "encoded-audio.log")
        if not re.search(r'Audio:\s*aac[^\n]*48000 Hz,\s*stereo', p.stderr):
            raise ValueError("Encoded audio must be AAC, 48kHz, stereo")
        summary = p.stderr[p.stderr.rfind("Summary:"):]
        loudness = float(re.search(r'I:\s*([-\d.]+) LUFS', summary).group(1))
        peak = float(re.search(r'Peak:\s*([-\d.]+) dBFS', summary).group(1))
        if abs(loudness - cfg["music"]["lufs"]) > 1.5 or peak >= -.1:
            raise ValueError(f"Review mastering: {loudness} LUFS, {peak} dBTP")
        raw = subprocess.run([self.ff, "-v", "error", "-i", str(self.film), "-map", "0:a:0", "-f", "f32le",
                              "-ac", "2", "-ar", "48000", "pipe:1"], capture_output=True)
        if raw.returncode or raw.stderr:
            raise RuntimeError("Encoded audio decode failed")
        audio = np.frombuffer(raw.stdout, dtype="<f4").reshape(-1, 2)
        if abs(len(audio) / 48000 - cfg["duration"]) > .04 or not np.isfinite(audio).all() or np.abs(audio).max() >= 1:
            raise ValueError("Encoded audio duration or sample validation failed")
        stereo_energy = float(np.mean(audio ** 2))
        mono_energy = float(np.mean(audio.mean(axis=1) ** 2))
        mono_loss = 10 * np.log10(mono_energy / max(stereo_energy, 1e-12))
        if mono_loss <= -3.5:
            raise ValueError("Excessive phase cancellation in mono")
        bins = [float(np.sqrt(np.mean(audio[k:k + 48000] ** 2))) for k in range(0, len(audio), 48000)]
        interior = bins[1:-2] if len(bins) >= 5 else bins[:-1]
        if interior and min(interior) < .0005:
            raise ValueError("Unexpected near-silent section; inspect the score")
        tail = audio[-min(len(audio), 2400):]
        tail_rms = float(np.sqrt(np.mean(tail ** 2)))
        if tail_rms > .01:
            raise ValueError("Ending is not sufficiently faded; inspect the final notes")

        from continuity import micro_dynamics
        sections = cfg.get("sections") or [{"start":s["start"],"end":s["end"],"role":s["music_role"]} for s in cfg["scenes"]]
        micro = micro_dynamics(audio, 48000, sections)
        folder = self.work / "qc"
        folder.mkdir(exist_ok=True)
        samples = [(s["start"] + (s["end"] - s["start"]) * .58) for s in cfg["scenes"]]
        for scene in cfg["scenes"][1:]:
            samples.extend(max(0., min(cfg["duration"] - 1 / cfg["fps"], scene["start"] + offset)) for offset in [-.4, 0., .4])
        samples += [max(0, cfg["duration"] - 1 / cfg["fps"])]
        tiles = []
        for i, time in enumerate(samples):
            path = folder / f"{i:02d}.png"
            self.run(["-v", "error", "-y", "-ss", str(time), "-i", str(self.film), "-frames:v", "1", str(path)], f"sample-{i:02d}.log")
            image = Image.open(path)
            if image.size != (cfg["width"], cfg["height"]):
                raise ValueError("Unexpected sample dimensions")
            tiles.append(image.resize((480, 270)))
        sheet = Image.new("RGB", (1440, ((len(tiles) + 2) // 3) * 270), "white")
        for i, tile in enumerate(tiles):
            sheet.paste(tile, (i % 3 * 480, i // 3 * 270))
        sheet.save(folder / "contact-sheet.jpg", quality=92)
        metrics = {"file": self.film.name, "duration_seconds": metadata["duration"], "width": metadata["size"][0],
                   "height": metadata["size"][1], "fps": metadata["fps"], "decoded_frames": int(frames[-1]), "decode_errors": 0,
                   "audio_codec": "aac", "audio_sample_rate": 48000, "audio_channels": 2,
                   "decoded_audio_seconds": round(len(audio) / 48000, 5), "integrated_loudness_lufs": loudness,
                   "true_peak_dbfs": peak, "mono_fold_down_db": round(float(mono_loss), 3), "micro_dynamics": micro,
                   "ending_rms_last_50ms": round(tail_rms, 6), "visual_samples_exported": len(samples),
                   "limits": "Signal checks and exported frames do not certify subjective music or design quality."}
        (self.out / f"{cfg['slug']}-qc.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        music = json.loads((self.work / "music-metadata.json").read_text(encoding="utf-8"))
        note = (f"# {cfg['name']}\n\n{cfg['duration']} 秒、{cfg['width']} × {cfg['height']}、{cfg['fps']}fps。\n\n"
                + f"配樂：原創 EDM，{music['bpm']} BPM，{music['key']}。\n音色來源：{music['instrument_source']}。\n\n"
                + f"實際 MP4 解碼 {metrics['decoded_frames']} 影格無錯誤；48kHz AAC 立體聲；"
                + f"{loudness} LUFS、{peak} dBTP。\n\n"
                + "畫面樣本位於 work/qc/；需實際檢查品牌、字型、數據與設計。訊號檢查不代表已試聽或判定音樂悅耳。\n"
                + "本案公司資料與素材來源應另記錄於 work/sources.json，交付時納入可讀的來源說明。\n")
        if music.get("soundfont_source"):
            note += "\n音色庫來源：" + music["soundfont_source"] + "\n"
        if music.get("soundfont_license_file"):
            note += "音色庫授權檔：" + music["soundfont_license_file"] + "\n"
        ledger = self.work / "sources.json"
        if ledger.exists():
            sources = json.loads(ledger.read_text(encoding="utf-8-sig"))
            if isinstance(sources, dict):
                sources = sources.get("sources", [])
            note += "\n## 本案來源\n\n"
            for source in sources:
                if source.get("url"):
                    claim = str(source.get("claim", source.get("publisher", "來源"))).replace("\n", " ")
                    note += f"- [{claim}]({source['url']})"
                    if source.get("checked_date"):
                        note += "；查核：" + str(source["checked_date"])
                    if source.get("scope"):
                        note += "；範圍：" + str(source["scope"])
                    note += "\n"
        (self.out / f"{cfg['slug']}-production.md").write_text(note, encoding="utf-8-sig")
        print("VERIFIED", json.dumps(metrics), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", type=Path, required=True)
    args = ap.parse_args()
    root, cfg = load(args.project)
    finisher = Finisher(root, cfg)
    finisher.master()
    finisher.mux()
    finisher.verify()
