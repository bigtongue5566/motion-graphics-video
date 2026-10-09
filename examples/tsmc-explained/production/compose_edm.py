"""Original, configurable melodic-house score with sample or synthesized keys."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess

import mido
import numpy as np
from scipy.io import wavfile

import instruments as ins
from projectlib import load, local_path, section_at, harmonic_material


class Score:
    def __init__(self, root, cfg):
        self.root, self.cfg = root, cfg
        self.duration = float(cfg["duration"])
        self.sr = ins.SR
        self.n = round(self.duration * self.sr)
        self.bpm = float(cfg["music"]["bpm"])
        self.beat, self.bar = 60 / self.bpm, 240 / self.bpm
        self.harmony_data, self.shift = harmonic_material(cfg["music"]["key"])
        ins.RNG = np.random.default_rng(cfg["music"].get("seed", 19712026))
        names = ["keys", "pad", "chords", "lead", "arp", "bass", "drums", "effects"]
        self.stems = {name: np.zeros((self.n, 2), np.float32) for name in names}
        self.events, self.kicks, self.harmony = [], [], []
        self.sf = local_path(root, cfg["music"].get("soundfont"))
        self.instrument_source = "synthesized keys and original electronic synthesis"
        cycle = 0
        prior = None
        count = math.ceil(self.duration / self.bar)
        for index in range(count):
            a, b = index * self.bar, min((index + 1) * self.bar, self.duration)
            role = section_at(cfg, min(a + .001, self.duration - 1e-6))[1]["role"]
            if role == "drop" and prior != "drop":
                cycle = 0
            name = cfg["music"]["progression"][cycle % len(cfg["music"]["progression"])]
            if role == "outro" or index == count - 1:
                name = "I" if cfg["music"]["key"].endswith("major") else "i"
            elif role == "build" and b < self.duration and section_at(cfg, b + .001)[1]["role"] == "drop":
                name = "V" if cfg["music"]["key"].endswith("major") else "VII"
            voices, bass, hook = self.harmony_data[name]
            self.harmony.append({"start": a, "end": b, "role": role, "name": name,
                                 "voices": [n + self.shift for n in voices], "root": bass + self.shift,
                                 "hook": [n + self.shift for n in hook], "pcs": {(n + self.shift) % 12 for n in voices}})
            cycle += 1
            prior = role

    def add(self, stem, start, sound, gain=1., pan=0.):
        sound = np.asarray(sound, np.float32)
        if sound.ndim == 1:
            theta = (pan + 1) * math.pi / 4
            sound = np.column_stack([sound * math.cos(theta), sound * math.sin(theta)])
        k = round(start * self.sr)
        count = min(len(sound), self.n - k)
        if k >= 0 and count > 0:
            self.stems[stem][k:k + count] += sound[:count] * gain

    def note(self, stem, time, length, pitch, gain, pan=0., velocity=80, sound=None, boundary=None):
        end = self.duration if boundary is None else min(self.duration, boundary)
        length = min(length, end - time)
        if length < .009:
            return
        if not 0 <= pitch <= 127:
            raise ValueError("Transposition moved a note outside MIDI range")
        self.events.append({"stem": stem, "time": time, "duration": length, "note": pitch, "velocity": velocity})
        if stem == "keys" and self.sf:
            return
        if sound is None:
            sound = ins.pluck(pitch, length, 1900.)
        rendered = np.asarray(sound[:round(length * self.sr)], dtype=np.float32)
        if rendered.ndim == 1:
            rendered = ins.soften(rendered, .003, min(.045, length / 4))
        else:
            rendered = np.column_stack([ins.soften(rendered[:, c], .003, min(.045, length / 4)) for c in range(2)])
        self.add(stem, time, rendered, gain, pan)

    def keys(self, pitch, length):
        t = np.arange(round(length * self.sr), dtype=np.float64) / self.sr
        f = ins.hz(pitch)
        sound = np.zeros_like(t)
        for partial, amplitude, decay in [(1, .75, 2.), (2, .18, 3.5), (3, .065, 5.), (4, .025, 8.)]:
            sound += amplitude * np.sin(2 * math.pi * f * partial * t) * np.exp(-t * decay)
        return ins.soften(sound, .005, min(.12, length / 3))

    def arrange(self):
        kick, clap, hat, opened = ins.kick(), ins.clap(), ins.hat(), ins.hat(True)
        for chord in self.harmony:
            a, b, role = chord["start"], chord["end"], chord["role"]
            span = b - a
            drop = role == "drop"
            for pitch in chord["voices"]:
                length = max(.01, span - min(.04, span / 5))
                self.note("pad", a, length, pitch + 12, .07 if drop else .105,
                          sound=ins.pad_voice(pitch + 12, length), boundary=b)

            if not drop:
                offsets = [0., .5, 1., 2., 2.5]
                pitches = [0, 1, 2, 1, 2]
                for j, (off, index) in enumerate(zip(offsets, pitches)):
                    start = a + off * self.beat
                    length = min(.95 * self.beat, b - start - min(.05, span / 8))
                    if length > .009:
                        pitch = chord["voices"][index] + 12
                        self.note("keys", start, length, pitch, .13 if j == 0 else .10,
                                  sound=self.keys(pitch, length), velocity=76 if j == 0 else 65, boundary=b)
                for pitch in chord["voices"]:
                    length = span * .80
                    self.note("keys", a, length, pitch, .075, sound=self.keys(pitch, length), velocity=47, boundary=b)

            if drop or role == "groove":
                phrase = [2, 1, 0, 1, 2, 1] if round(a / self.bar) % 2 == 0 else [1, 2, 1, 0, 1, 2]
                for j, (off, beats, degree) in enumerate(zip([0., .75, 1.5, 2., 2.5, 3.25], [.60, .35, .42, .30, .50, .55], phrase)):
                    start, length = a + off * self.beat, beats * self.beat
                    pitch = chord["voices"][degree] + 12
                    self.note("lead", start, length, pitch, .37 if drop else .16,
                              -.10 if j % 2 else .10, sound=ins.pluck(pitch, length, 2100. if drop else 1500.), boundary=b)
            pulse = drop or role in ("groove", "build")
            for beat in range(4):
                start = a + beat * self.beat
                if start >= b:
                    break
                current_role = section_at(self.cfg, start + 1e-7)[1]["role"]
                on = current_role in ("drop", "groove", "build")
                if on:
                    self.add("drums", start, kick, .69 if current_role == "drop" else .45)
                    self.kicks.append(start)
                    self.events.append({"stem": "drums", "time": start, "duration": min(.15, b - start), "note": 36, "velocity": 98})
                    if beat % 2:
                        self.add("drums", start, clap, .68 if drop else .43)
                        self.events.append({"stem": "drums", "time": start, "duration": min(.12, b - start), "note": 39, "velocity": 78})
                off = start + self.beat * .5
                if on and off < b:
                    self.add("drums", off, opened if drop else hat, .60 if drop else .41, .20)
                    self.events.append({"stem": "drums", "time": off, "duration": min(.10, b - off), "note": 46 if drop else 42, "velocity": 67})
                if pulse:
                    length = min(self.beat * .46, b - off - .008)
                    if length > .01:
                        self.note("bass", off, length, chord["root"], .48 if drop else .36,
                                  sound=ins.bass_note(chord["root"], length), boundary=b)
                        for pitch in chord["voices"]:
                            self.note("chords", off, length, pitch + 12, .19 if drop else .115,
                                      sound=ins.chord_voice(pitch + 12, length, drop), boundary=b)
            if role == "build" or drop:
                for j in range(8):
                    start, length = a + j * self.beat / 2, min(.21, self.beat * .43)
                    pitch = chord["voices"][[0, 1, 2, 1][j % 4]] + 12
                    self.note("arp", start, length, pitch, .025 if drop else .032, .32 if j % 2 else -.32,
                              sound=ins.pluck(pitch, length, 1400.), boundary=b)

        # Musical section accents follow exact requested timings, including non-bar boundaries.
        for i, section in enumerate(self.cfg["sections"]):
            start = section["start"]
            if i and section["role"] in ("drop", "groove", "outro"):
                self.add("effects", start, ins.crash(), .29)
            if i and section["role"] == "drop":
                length = min(1.75, start, self.cfg["sections"][i - 1]["end"] - self.cfg["sections"][i - 1]["start"])
                if length > .1:
                    self.add("effects", start - length, ins.swell(length), .65)
        if self.sf:
            self.render_sampled_keys()

    def write_midi(self, target, keys_only=False):
        midi = mido.MidiFile(type=1, ticks_per_beat=480, charset="utf-8")
        meta = mido.MidiTrack()
        meta.append(mido.MetaMessage("track_name", name=self.cfg["name"] + " - Original EDM"))
        meta.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(self.bpm)))
        meta.append(mido.MetaMessage("time_signature", numerator=4, denominator=4))
        meta.append(mido.MetaMessage("key_signature", key=self.cfg["music"]["key"].split()[0] + ("m" if self.cfg["music"]["key"].endswith("minor") else "")))
        midi.tracks.append(meta)
        channels = {"keys": (0, 0), "pad": (1, 89), "chords": (2, 81), "lead": (3, 80),
                    "arp": (4, 98), "bass": (5, 38), "drums": (9, 0)}
        for name, (channel, program) in channels.items():
            if keys_only and name != "keys":
                continue
            track = mido.MidiTrack()
            track.append(mido.MetaMessage("track_name", name=name))
            track.append(mido.Message("program_change", channel=channel, program=program))
            for control in [91, 93]:
                track.append(mido.Message("control_change", channel=channel, control=control, value=0))
            queue = []
            for event in [e for e in self.events if e["stem"] == name]:
                for start, priority, type_ in [(event["time"], 2, "note_on"), (event["time"] + event["duration"], 0, "note_off")]:
                    message = mido.Message(type_, channel=channel, note=event["note"], velocity=event["velocity"] if type_ == "note_on" else 0)
                    queue.append((round(start / self.beat * 480), priority, message))
            if name == "keys":
                for chord in self.harmony[1:]:
                    queue.append((round(chord["start"] / self.beat * 480), 1,
                                  mido.Message("control_change", channel=channel, control=120, value=0)))
            previous = 0
            for tick, _, message in sorted(queue, key=lambda item: (item[0], item[1])):
                message.time = tick - previous
                track.append(message)
                previous = tick
            track.append(mido.MetaMessage("end_of_track", time=max(0, round(self.duration / self.beat * 480) - previous)))
            midi.tracks.append(track)
        midi.save(target)

    def render_sampled_keys(self):
        with self.sf.open("rb") as stream:
            header = stream.read(12)
        if header[:4] != b"RIFF" or header[8:12] != b"sfbk" or int.from_bytes(header[4:8], "little") + 8 != self.sf.stat().st_size:
            raise ValueError("Incomplete or invalid SoundFont")
        exe = local_path(self.root, self.cfg["music"].get("fluidsynth")) or shutil.which("fluidsynth")
        if not exe:
            raise FileNotFoundError("Set music.fluidsynth or install a compatible FluidSynth")
        midi = self.root / "work" / "keys.mid"
        target = self.root / "work" / "keys-render.wav"
        self.write_midi(midi, keys_only=True)
        p = subprocess.run([str(exe), "-ni", "-F", str(target), "-T", "wav", "-O", "float", "-r", str(self.sr),
                            "-g", ".5", "-R", "0", "-C", "0", str(self.sf), str(midi)], capture_output=True)
        (self.root / "work" / "sampled-keys.log").write_bytes(p.stdout + b"\n" + p.stderr)
        if p.returncode:
            raise RuntimeError("FluidSynth rendering failed; see sampled-keys.log")
        rate, sound = wavfile.read(target)
        if rate != self.sr or sound.ndim != 2 or sound.shape[1] != 2:
            raise ValueError("Unexpected sampled instrument format")
        if sound.dtype != np.float32:
            sound = sound.astype(np.float32) / np.iinfo(sound.dtype).max()
        count = min(len(sound), self.n)
        self.stems["keys"][:count] = sound[:count] * 2.5
        for chord in self.harmony[1:]:
            k, r = round(chord["start"] * self.sr), min(round(.024 * self.sr), round(self.bar * self.sr / 4))
            self.stems["keys"][k - r:k] *= np.cos(np.linspace(0, math.pi / 2, r))[:, None] ** 2
            a = min(round(.006 * self.sr), self.n - k)
            self.stems["keys"][k:k + a] *= np.sin(np.linspace(0, math.pi / 2, a))[:, None] ** 2
        self.instrument_source = "FluidSynth piano using " + self.sf.name + "; original electronic synthesis"

    def mix(self):
        for name, cutoff in [("keys", 140), ("pad", 230), ("chords", 220), ("lead", 350), ("arp", 420)]:
            self.stems[name] = ins.filt(self.stems[name], cutoff)
        self.stems["bass"] = ins.filt(self.stems["bass"], 230, "lowpass")
        duck = np.ones(self.n, np.float32)
        t = np.arange(round(min(.35, self.beat * .7) * self.sr)) / self.sr
        reduction = 1 - .63 * np.exp(-t * 13)
        ramp = min(len(t), round(.004 * self.sr))
        reduction[:ramp] = np.linspace(1, reduction[min(ramp, len(t) - 1)], ramp)
        for start in self.kicks:
            k = round(start * self.sr)
            size = min(len(t), self.n - k)
            duck[k:k + size] = np.minimum(duck[k:k + size], reduction[:size])
        for name, depth in [("bass", 1.), ("chords", .8), ("pad", .65), ("arp", .4)]:
            self.stems[name] *= (1 - (1 - duck) * depth)[:, None]
        audio = sum(self.stems.values())
        intro = min(round(.1 * self.sr), self.n)
        ending = min(round(2.2 * self.sr), round(self.n * .24))
        audio[:intro] *= np.sin(np.linspace(0, math.pi / 2, intro))[:, None] ** 2
        audio[-ending:] *= np.cos(np.linspace(0, math.pi / 2, ending))[:, None] ** 2
        peak = float(np.abs(audio).max())
        headroom = .78 / max(.78, peak)
        wavfile.write(self.root / "work" / "score-mix.wav", self.sr, (audio * headroom).astype(np.float32))
        if self.cfg["music"].get("export_stems", False):
            folder = self.root / "outputs" / "stems"
            folder.mkdir(exist_ok=True)
            # Shared gain and fades preserve the relationship to the premaster mix.
            for name, stem in self.stems.items():
                stem[:intro] *= np.sin(np.linspace(0, math.pi / 2, intro))[:, None] ** 2
                stem[-ending:] *= np.cos(np.linspace(0, math.pi / 2, ending))[:, None] ** 2
                wavfile.write(folder / f"{self.cfg['slug']}-{name}.wav", self.sr, (stem * headroom).astype(np.float32))

    def audit(self):
        conflicts = []
        for event in self.events:
            if event["stem"] == "drums":
                continue
            for chord in self.harmony:
                if event["time"] < chord["end"] - 1e-7 and event["time"] + event["duration"] > chord["start"] + 1e-7:
                    if event["note"] % 12 not in chord["pcs"]:
                        conflicts.append(event)
        if conflicts:
            raise ValueError("Unexpected chord conflicts in this simple triad arrangement")
        key = self.cfg["music"]["key"]
        metadata = {"duration_seconds": self.duration, "bpm": self.bpm, "key": key, "original_composition": True,
                    "instrument_source": self.instrument_source, "soundfont_source": self.cfg["music"].get("soundfont_source"),
                    "soundfont_sha256": hashlib.sha256(self.sf.read_bytes()).hexdigest() if self.sf else None,
                    "soundfont_license_file": Path(self.cfg["music"]["license"]).name if self.cfg["music"].get("license") else None,
                    "note_events": len(self.events), "unexpected_chord_conflicts": len(conflicts),
                    "limits": "Symbolic note and signal checks do not establish listening quality.",
                    "harmony": [{k: v for k, v in c.items() if k != "pcs"} for c in self.harmony]}
        (self.root / "work" / "note-events.json").write_text(json.dumps(self.events, indent=2), encoding="utf-8")
        (self.root / "work" / "music-metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        print("MUSIC_AUDIT", json.dumps({k: metadata[k] for k in ["duration_seconds", "bpm", "key", "note_events", "unexpected_chord_conflicts"]}), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", type=Path, required=True)
    args = ap.parse_args()
    root, cfg = load(args.project)
    score = Score(root, cfg)
    score.arrange()
    score.audit()
    score.mix()
    score.write_midi(root / "outputs" / f"{cfg['slug']}-music.mid")
    print("MUSIC_COMPLETE", flush=True)
