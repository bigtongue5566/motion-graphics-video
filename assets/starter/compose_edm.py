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
from projectlib import load, local_path, scene_at


class Score:
    def __init__(self, root, cfg):
        self.root, self.cfg = root, cfg
        self.duration = float(cfg["duration"])
        self.sr = ins.SR
        self.n = round(self.duration * self.sr)
        self.bpm = float(cfg["music"]["bpm"])
        self.beat, self.bar = 60 / self.bpm, 240 / self.bpm
        self.shift = int(cfg["music"].get("transpose", 0))
        names = ["keys", "pad", "chords", "lead", "arp", "bass", "drums", "effects"]
        self.stems = {name: np.zeros((self.n, 2), np.float32) for name in names}
        self.events, self.kicks, self.harmony = [], [], []
        self.sf = local_path(root, cfg["music"].get("soundfont"))
        self.instrument_source = "synthesized keys and original electronic synthesis"
        self.harmony_data = {
            "G": ([55, 59, 62], 43, [71, 74, 79, 74]),
            "D": ([54, 57, 62], 38, [69, 74, 78, 74]),
            "Em": ([55, 59, 64], 40, [71, 76, 79, 76]),
            "C": ([55, 60, 64], 36, [67, 72, 76, 72]),
        }
        cycle = 0
        prior = None
        count = math.ceil(self.duration / self.bar)
        for index in range(count):
            a, b = index * self.bar, min((index + 1) * self.bar, self.duration)
            role = scene_at(cfg, min(a + .001, self.duration - 1e-6))[1]["music_role"]
            if role == "drop" and prior != "drop":
                cycle = 0
            name = ["G", "D", "Em", "C"][cycle % 4]
            if role == "outro" or index == count - 1:
                name = "G"
            elif role == "build" and b < self.duration and scene_at(cfg, b + .001)[1]["music_role"] == "drop":
                name = "D"
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
        from continuity import tail_end
        end = self.duration if boundary is None else min(self.duration, boundary)
        gate = min(length, end - time)
        if gate < .009:
            return
        if not 0 <= pitch <= 127:
            raise ValueError("Transposition moved a note outside MIDI range")
        event = {"stem":stem,"time":time,"duration":gate,"note":pitch,"velocity":velocity}
        self.events.append(event)
        if stem == "keys" and self.sf:
            return
        if sound is None:
            sound = ins.pluck(pitch, gate, 1900.)
        sound = np.asarray(sound, dtype=np.float32)
        desired = min(self.duration, time + len(sound)/self.sr)
        audible_end = tail_end(self.harmony, pitch, time+gate, desired)
        count = max(0, round((audible_end-time)*self.sr))
        rendered = sound[:count]
        if count < len(sound):
            if rendered.ndim == 1:
                rendered = ins.soften(rendered, .002, min(.025, len(rendered)/self.sr/3))
            else:
                rendered = np.column_stack([ins.soften(rendered[:,c], .002, min(.025, len(rendered)/self.sr/3)) for c in range(2)])
        event["sounding_duration"] = len(rendered)/self.sr
        self.add(stem, time, rendered, gain, pan)

    def keys(self, pitch, length):
        t = np.arange(round((length + .25) * self.sr), dtype=np.float64) / self.sr
        f = ins.hz(pitch)
        sound = np.zeros_like(t)
        for partial, amplitude, decay in [(1, .75, 2.), (2, .18, 3.5), (3, .065, 5.), (4, .025, 8.)]:
            sound += amplitude * np.sin(2 * math.pi * f * partial * t) * np.exp(-t * decay)
        return ins.release_shape(sound, length, .005, .25)

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
                for j, (off, beats, pitch) in enumerate(zip([0., 1.5, 2., 3.], [1.08, .4, .8, .84], chord["hook"])):
                    start, length = a + off * self.beat, beats * self.beat
                    pitch -= 0 if drop else 12
                    self.note("lead", start, length, pitch, .42 if drop else .19,
                              -.09 if j % 2 else .09, sound=ins.pluck(pitch, length, 2400. if drop else 1600.), boundary=b)
            pulse = drop or role in ("groove", "build")
            for beat in range(4):
                start = a + beat * self.beat
                if start >= b:
                    break
                current_role = scene_at(self.cfg, start + 1e-7)[1]["music_role"]
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

        # Chapter accents are placed at the exact video cuts, even for non-bar cuts.
        for i, scene in enumerate(self.cfg["scenes"]):
            start = scene["start"]
            if i and scene["music_role"] in ("drop", "groove", "outro"):
                self.add("effects", start, ins.crash(), .40)
            if i and scene["music_role"] == "drop":
                length = min(1.75, start, self.cfg["scenes"][i - 1]["end"] - self.cfg["scenes"][i - 1]["start"])
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
        keys = ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
        meta.append(mido.MetaMessage("key_signature", key=keys[(7 + self.shift) % 12]))
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
            previous = 0
            for tick, _, message in sorted(queue, key=lambda item: (item[0], item[1])):
                message.time = tick - previous
                track.append(message)
                previous = tick
            track.append(mido.MetaMessage("end_of_track", time=max(0, round(self.duration / self.beat * 480) - previous)))
            midi.tracks.append(track)
        midi.save(target)

    def render_sampled_keys(self):
        header = self.sf.read_bytes()[:12]
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
        # Preserve the instrument's own note-off release. A chord boundary
        # is not a reason to fade the entire sampled-instrument bus.
        self.instrument_source = "FluidSynth piano using " + self.sf.name + "; original electronic synthesis"

    def mix(self):
        for name, cutoff in [("keys", 140), ("pad", 230), ("chords", 220), ("lead", 350), ("arp", 420)]:
            self.stems[name] = ins.filt(self.stems[name], cutoff)
        self.stems["bass"] = ins.filt(self.stems["bass"], 230, "lowpass")
        duck = np.ones(self.n, np.float32)
        t = np.arange(round(min(.35, self.beat * .7) * self.sr)) / self.sr
        reduction = 1 - .63 * np.exp(-t * 13)
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
        audio *= .78 / max(.78, peak)
        wavfile.write(self.root / "work" / "score-mix.wav", self.sr, audio.astype(np.float32))

    def audit(self):
        from harmonic_comfort import check_profile
        consonance = check_profile(self.events, self.cfg["music"])
        conflicts = []
        for event in self.events:
            if event["stem"] == "drums":
                continue
            for chord in self.harmony:
                if event["time"] < chord["end"] - 1/self.sr and event["time"] + event.get("sounding_duration", event["duration"]) > chord["start"] + 1/self.sr:
                    if event["note"] % 12 not in chord["pcs"]:
                        conflicts.append(event)
        if conflicts:
            raise ValueError("Unexpected chord conflicts in this simple triad arrangement")
        key = ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"][(7 + self.shift) % 12] + " major"
        metadata = {"duration_seconds": self.duration, "bpm": self.bpm, "key": key, "original_composition": True,
                    "instrument_source": self.instrument_source, "soundfont_source": self.cfg["music"].get("soundfont_source"),
                    "soundfont_sha256": hashlib.sha256(self.sf.read_bytes()).hexdigest() if self.sf else None,
                    "soundfont_license_file": Path(self.cfg["music"]["license"]).name if self.cfg["music"].get("license") else None,
                    "note_events": len(self.events), "unexpected_chord_conflicts": len(conflicts),
                    "consonance_check": consonance,
                    "limits": "Symbolic note and signal checks do not establish listening quality.",
                    "harmony": [{k: v for k, v in c.items() if k != "pcs"} for c in self.harmony]}
        (self.root / "work" / "music-metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        print("MUSIC_AUDIT", json.dumps({k: metadata[k] for k in ["duration_seconds", "bpm", "key", "note_events", "unexpected_chord_conflicts"]}), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", type=Path, required=True)
    args = ap.parse_args()
    root, cfg = load(args.project)
    score = Score(root, cfg)
    score.arrange()
    from continuity import apply_continuity
    apply_continuity(score)
    score.audit()
    score.mix()
    score.write_midi(root / "outputs" / f"{cfg['slug']}-music.mid")
    print("MUSIC_COMPLETE", flush=True)
