"""Audio-only mastering and direct WAV/AAC quality checks; no video required."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import wave

import imageio_ffmpeg
import numpy as np

from projectlib import load


class Master:
    def __init__(self, root, cfg):
        self.root, self.cfg = root, cfg
        self.work, self.out = root / "work", root / "outputs"
        self.ff = imageio_ffmpeg.get_ffmpeg_exe()
        self.wav = self.out / f"{cfg['slug']}-master.wav"
        self.aac = self.out / f"{cfg['slug']}.m4a"

    def run(self, args, log):
        p = subprocess.run([self.ff, "-hide_banner", "-nostats", *args], capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
        (self.work / log).write_text(p.stdout + "\n" + p.stderr, encoding="utf-8")
        if p.returncode:
            raise RuntimeError(p.stderr[-2400:])
        return p

    def render(self):
        music = self.cfg["music"]
        base = f"loudnorm=I={music['lufs']}:TP={music['true_peak']}:LRA=9"
        first = self.run(["-i", str(self.work / "score-mix.wav"), "-af", base + ":print_format=json",
                          "-f", "null", "-"], "loudness-analysis.log")
        values = json.loads(re.search(r'\{\s*"input_i".*?\}', first.stderr, re.S).group(0))
        if not np.isfinite([float(values[k]) for k in ["input_i", "input_tp", "input_lra", "input_thresh", "target_offset"]]).all():
            raise ValueError("The mix cannot be mastered: inspect silence or non-finite samples")
        filter_ = base + ":" + ":".join(f"{key}={values[value]}" for key, value in [
            ("measured_I", "input_i"), ("measured_TP", "input_tp"), ("measured_LRA", "input_lra"),
            ("measured_thresh", "input_thresh"), ("offset", "target_offset")]) + ":linear=true:print_format=json"
        self.run(["-y", "-i", str(self.work / "score-mix.wav"), "-af", filter_, "-ar", "48000", "-ac", "2",
                  "-c:a", "pcm_s24le", "-t", str(self.cfg["duration"]), str(self.wav)], "mastering.log")
        self.run(["-y", "-i", str(self.wav), "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2",
                  "-movflags", "+faststart", "-metadata", "title=" + self.cfg["name"],
                  "-metadata", "comment=Original electronic Demo composition; see music provenance.", str(self.aac)], "aac-encoding.log")
        print("AUDIO_MASTERED", flush=True)

    def measure(self, path):
        p = self.run(["-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"], path.stem + "-meter.log")
        summary = p.stderr[p.stderr.rfind("Summary:"):]
        loudness = float(re.search(r'I:\s*([-\d.]+) LUFS', summary).group(1))
        peak = float(re.search(r'Peak:\s*([-\d.]+) dBFS', summary).group(1))
        lra = float(re.search(r'LRA:\s*([-\d.]+) LU', summary).group(1))
        if not np.isfinite([loudness, peak, lra]).all():
            raise ValueError("Non-finite audio measurements")
        if abs(loudness - self.cfg["music"]["lufs"]) > 1.5:
            raise ValueError(f"Review loudness: {loudness} LUFS")
        if peak >= -.1 or peak > self.cfg["music"]["true_peak"] + .9:
            raise ValueError(f"Review encoded true peak: {peak} dBTP")
        return {"integrated_lufs": loudness, "true_peak_dbfs": peak, "loudness_range_lu": lra}, p.stderr

    def decode(self, path):
        p = subprocess.run([self.ff, "-v", "error", "-i", str(path), "-map", "0:a:0", "-f", "f32le",
                            "-ac", "2", "-ar", "48000", "pipe:1"], capture_output=True)
        if p.returncode or p.stderr:
            raise RuntimeError("Full audio decode failed")
        sound = np.frombuffer(p.stdout, dtype="<f4").reshape(-1, 2)
        if not np.isfinite(sound).all() or float(np.abs(sound).max()) >= 1:
            raise ValueError("Invalid or clipped decoded samples")
        return sound

    def verify(self):
        with wave.open(str(self.wav), "rb") as source:
            props = {"sample_rate": source.getframerate(), "channels": source.getnchannels(),
                     "sample_width_bytes": source.getsampwidth(), "samples": source.getnframes()}
        expected = round(self.cfg["duration"] * 48000)
        if props != {"sample_rate": 48000, "channels": 2, "sample_width_bytes": 3, "samples": expected}:
            raise ValueError("WAV master does not have the requested sample count and 24-bit stereo format")
        wav_levels, _ = self.measure(self.wav)
        aac_levels, log = self.measure(self.aac)
        if not re.search(r'Audio:\s*aac[^\n]*48000 Hz,\s*stereo', log):
            raise ValueError("Expected 48kHz stereo AAC stream")
        self.decode(self.wav)
        sound = self.decode(self.aac)
        seconds = len(sound) / 48000
        if abs(seconds - self.cfg["duration"]) > 1024 / 48000 + .001:
            raise ValueError("AAC decoded duration differs beyond codec frame padding")
        energy = float(np.mean(sound ** 2))
        mono = float(np.mean(sound.mean(axis=1) ** 2))
        mono_loss = 10 * np.log10(mono / max(energy, 1e-12))
        if mono_loss < -3.5:
            raise ValueError("Excessive phase cancellation when summed to mono")
        bins = [float(np.sqrt(np.mean(sound[k:k + 48000] ** 2))) for k in range(0, len(sound), 48000)]
        interior = bins[1:-2] if len(bins) >= 5 else bins[:-1]
        near_silent = [i + 1 for i, rms in enumerate(interior) if rms < .0005]
        if near_silent:
            raise ValueError(f"Review unexpected near-silence around seconds {near_silent}")
        tail_rms = float(np.sqrt(np.mean(sound[-min(len(sound), 2400):] ** 2)))
        if tail_rms > .01:
            raise ValueError("Inspect ending fade")
        music = json.loads((self.work / "music-metadata.json").read_text(encoding="utf-8"))
        metrics = {"name": self.cfg["name"], "requested_seconds": self.cfg["duration"],
                   "wav": {"file": self.wav.name, "duration_seconds": props["samples"] / 48000, **props, **wav_levels},
                   "aac": {"file": self.aac.name, "decoded_seconds": round(seconds, 5), **aac_levels},
                   "full_decode_errors": 0, "mono_fold_down_db": round(float(mono_loss), 3),
                   "ending_rms_last_50ms": round(tail_rms, 6), "unexpected_near_silent_seconds": near_silent,
                   "bpm": music["bpm"], "key": music["key"], "unexpected_chord_conflicts": music["unexpected_chord_conflicts"],
                   "aac_sha256": hashlib.sha256(self.aac.read_bytes()).hexdigest(),
                   "limits": "Objective QC does not certify listening quality."}
        (self.out / f"{self.cfg['slug']}-qc.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
        provenance = {"composition": "original " + self.cfg["music"]["style"] + " Demo arrangement", "bpm": music["bpm"], "key": music["key"],
                      "instrument_source": music["instrument_source"], "soundfont_source": music.get("soundfont_source"),
                      "soundfont_sha256": music.get("soundfont_sha256"), "soundfont_license_file": music.get("soundfont_license_file"),
                      "sections": self.cfg["sections"],
                      "midi_note": "GM instrument suggestions; MIDI playback will not reproduce the custom synthesized audio.",
                      "stem_note": "Float32 premaster stems share gain and fades; they are not separately loudness normalized."}
        (self.out / f"{self.cfg['slug']}-provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")
        note = (f"# {self.cfg['name']}\n\n{self.cfg['duration']} 秒，{music['bpm']} BPM，{music['key']}。\n\n"
                + f"音色來源：{music['instrument_source']}。\n\n"
                + f"WAV 母帶：48kHz、24-bit、立體聲，{wav_levels['integrated_lufs']} LUFS。\n"
                + f"AAC：{aac_levels['integrated_lufs']} LUFS、{aac_levels['true_peak_dbfs']} dBTP；完整解碼無錯誤。\n\n"
                + "MIDI 保存各聲部音符；預設 GM 音色與完成版合成器不同。分軌若有輸出，為共同增益的浮點 premaster，可用於重新混音。\n\n"
                + "音符與訊號檢查用來排除製作錯誤；音樂的主觀聽感需實際播放判斷。本檢查不代表已試聽。\n")
        if music.get("soundfont_source"):
            note += "\n音色庫來源：" + music["soundfont_source"] + "\n"
        (self.out / f"{self.cfg['slug']}-production.md").write_text(note, encoding="utf-8-sig")
        print("AUDIO_VERIFIED", json.dumps(metrics, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", type=Path, required=True)
    args = ap.parse_args()
    root, cfg = load(args.project)
    master = Master(root, cfg)
    master.render()
    master.verify()
