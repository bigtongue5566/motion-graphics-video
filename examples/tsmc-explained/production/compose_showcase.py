"""Four bespoke, original showcase arrangements; not renamed starter presets.

The JSON chord library includes the deliberately voiced sevenths and ninths.
Every pitched onset, echo and its sounding duration is exported for review.
"""
import argparse
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.io import wavfile

import instruments as ins
from compose_edm import Score
from projectlib import load


@lru_cache(maxsize=128)
def glass(note, duration):
    t = np.arange(round(duration * ins.SR)) / ins.SR
    f = ins.hz(note)
    # Harmonic overtones, with the brighter attack decaying before the body.
    y = sum(w * np.sin(2 * math.pi * h * f * t + h * .11) * np.exp(-t * decay)
            for h, w, decay in [(1, .62, 1.5), (2, .18, 4), (3, .08, 8), (4, .035, 13)])
    return ins.soften(y, .014, min(.16, duration / 3))


@lru_cache(maxsize=128)
def air_saw(note, duration, cutoff):
    """Band-limited detuned poly voice, with no free-running sub oscillator."""
    t = np.arange(round(duration * ins.SR)) / ins.SR
    f = ins.hz(note)
    y = np.zeros((len(t), 2), np.float64)
    for c in range(2):
        for v, cents in enumerate([-8, 0, 8]):
            frequency = f * 2 ** ((cents + (1.5 if c else -1.5)) / 1200)
            for h in range(1, min(30, int(16000 / frequency)) + 1):
                weight = .10 / h ** 1.13 / math.sqrt(1 + (h * frequency / cutoff) ** 6)
                y[:, c] += weight * np.sin(2 * math.pi * h * frequency * t + v * 1.7 + h * .21 + c * .1)
        y[:, c] = ins.soften(y[:, c], .024, min(.09, duration / 4))
    return y.astype(np.float32)


@lru_cache(maxsize=128)
def ribbon(note, duration):
    t = np.arange(round(duration * ins.SR)) / ins.SR
    f = ins.hz(note)
    y = np.sin(2 * math.pi * f * t + .16 * np.sin(2 * math.pi * 5 * t))
    y += .19 * np.sin(2 * math.pi * f * 2 * t) + .075 * np.sin(2 * math.pi * f * 3 * t)
    return ins.soften(y * .37 * (.86 + .14 * np.exp(-t * 7)), .025, min(.10, duration / 3))


@lru_cache(maxsize=128)
def sub(note, duration, clipped=False):
    t = np.arange(round(duration * ins.SR)) / ins.SR
    y = np.sin(2 * math.pi * ins.hz(note) * t)
    if clipped:
        y = np.tanh(y * 1.4) * np.exp(-t * 3.0)
    return ins.soften(y * .65, .010, min(.065, duration / 3))


@lru_cache(maxsize=128)
def reese_mid(note, duration, cutoff):
    t = np.arange(round(duration * ins.SR)) / ins.SR
    f = ins.hz(note)
    y = np.zeros(len(t))
    for cents in [-10, 10]:
        detune = 2 ** (cents / 1200)
        for h in range(2, min(24, int(12000 / (f * detune))) + 1):
            y += .42 / h ** 1.18 * np.sin(2 * math.pi * h * f * detune * t + .23 * h)
    y = ins.filt(np.tanh(y * 1.7), [125, cutoff], "bandpass")
    y *= .34 * (.78 + .22 * np.sin(2 * math.pi * 1.8 * t))
    return ins.soften(y, .014, min(.075, duration / 3))


@lru_cache(maxsize=128)
def dub_voice(note, duration, cutoff):
    t = np.arange(round(duration * ins.SR)) / ins.SR
    f = ins.hz(note)
    y = np.zeros((len(t), 2))
    # Short, dark stab with small stereo detuning; echo copies are separately voiced.
    for c, cents in enumerate([-3, 3]):
        frequency = f * 2 ** (cents / 1200)
        for h in range(1, min(22, int(15000 / frequency)) + 1):
            weight = .35 / h ** 1.24 / math.sqrt(1 + (h * frequency / cutoff) ** 6)
            y[:, c] += weight * np.sin(2 * math.pi * frequency * h * t + .4 * h)
        y[:, c] *= np.exp(-t * 7)
        y[:, c] = ins.soften(y[:, c], .012, min(.12, duration / 3))
    return y.astype(np.float32)


def rim():
    t = np.arange(round(.07 * ins.SR)) / ins.SR
    noise = ins.filt(ins.RNG.standard_normal(len(t)), [1500, 5500], "bandpass")
    return ins.soften((noise * .025 + np.sin(2 * math.pi * 760 * t) * .06) * np.exp(-t * 85), .001, .015)


class Showcase(Score):
    def __init__(self, root, cfg):
        super().__init__(root, cfg)
        self.identity = cfg["music"]["identity"]
        self.instrument_source = "original oscillators and generated percussion noise; no sampled recordings"
        self.automation = []
        self.harmony = []
        chords = cfg["music"]["voiced_chords"]
        span_bars = 4 if self.identity == "dub-techno" else 2
        cycle = 0
        for si, section in enumerate(cfg["sections"]):
            a = section["start"]
            while a < section["end"] - 1e-7:
                b = min(section["end"], a + span_bars * self.bar)
                index = 0 if section["role"] == "outro" else cycle % len(chords)
                chord = chords[index]
                pitches = chord["voices"]
                self.harmony.append({"start": a, "end": b, "role": section["role"],
                                     "name": chord["name"], "voices": pitches, "root": chord["root"],
                                     "pcs": {n % 12 for n in pitches + [chord["root"]]}, "section": si})
                cycle += 1
                a = b
        self.percussion = {"kick": ins.tight_kick(self.identity == "drum-and-bass"),
                           "snare": ins.snare(self.identity == "drum-and-bass"),
                           "clap": ins.clap(), "hat": ins.hat(), "open": ins.hat(True), "rim": rim()}
        if self.identity == "future-bass":
            self.percussion["kick"] = ins.kick()
        if self.identity == "dub-techno":
            # Darker, longer body for the steady pulse; hats are also less bright.
            self.percussion["kick"] = ins.filt(ins.kick(), 1400, "lowpass")
            self.percussion["hat"] = ins.filt(self.percussion["hat"], 10000, "lowpass")

    def drum(self, a, off, kind, gain, boundary, pan=0, velocity=80):
        time = a + off * self.beat
        if time >= boundary - .025:
            return
        sound = self.percussion[kind]
        length = min(len(sound) / self.sr, boundary - time)
        self.add("drums", time, ins.soften(sound[:round(length * self.sr)], .001, min(.025, length / 3)), gain, pan)
        self.events.append({"stem": "drums", "time": time, "duration": length,
                            "note": {"kick": 36, "snare": 38, "clap": 39, "hat": 42, "open": 46, "rim": 37}[kind],
                            "velocity": velocity})
        if kind == "kick":
            self.kicks.append(time)

    def pitched(self, stem, chord, start, length, note, gain, voice, pan=0, **params):
        length = min(length, chord["end"] - start - .012)
        if length < .025:
            return
        sound = voice(note, length, **params)
        self.note(stem, start, length, note, gain, pan, velocity=max(1, min(115, round(54 + gain * 38))),
                  sound=sound, boundary=chord["end"])

    def pad(self, chord, gain, octave=12):
        span = chord["end"] - chord["start"] - .025
        for pitch in chord["voices"]:
            self.pitched("pad", chord, chord["start"], span, pitch + octave, gain, ins.pad_voice)

    def future(self, chord):
        a, b, role = chord["start"], chord["end"], chord["role"]
        active = role in ("groove", "build", "drop")
        strong = role == "drop"
        self.pad(chord, .07 if strong else .10)
        if not strong:
            for j, off in enumerate([0, 1.5, 3.25, 4.5, 6]):
                pitch = chord["voices"][[0, 3, 1, 4, 2][j]] + 12
                self.pitched("keys", chord, a + off * self.beat, 1.5 * self.beat, pitch,
                             .23 if role in ("intro", "break", "outro") else .15, glass, (-1) ** j * .15)
        for local in range(math.ceil((b - a) / self.bar)):
            t = a + local * self.bar
            end = min(t + self.bar, b)
            bar = round(t / self.bar)
            if active:
                kicks = [0, 1.5, 3.25] if strong and bar % 2 else [0, 2.75]
                for off in kicks:
                    self.drum(t, off, "kick", .72 if strong else .46, end, velocity=105)
                self.drum(t, 2, "snare", 1.03 if strong else .60, end, velocity=108)
                self.drum(t, 2.025, "clap", .46 if strong else .25, end, .07)
                hats = [0, .5, 1, 1.5, 2, 2.5, 3, 3.5]
                for j, off in enumerate(hats):
                    self.drum(t, off, "hat", .66 if j % 2 else .40, end, (-1) ** j * .18, 69 if j % 2 else 48)
                if strong and bar % 4 == 3:
                    for off in [3.25, 3.375, 3.625, 3.75, 3.875]:
                        self.drum(t, off, "hat", .50, end, .13, 50)
                for off, beats in [(0, 1.25), (1.5, .5), (2.75, .75), (3.5, .35)]:
                    pitch = chord["root"] + (12 if bar % 4 == 3 and off == 3.5 else 0)
                    self.pitched("bass", chord, t + off * self.beat, beats * self.beat, pitch,
                                 .53 if strong else .32, sub)
            if strong or role == "build":
                cutoff = 2600 if strong else 900 + (t - self.cfg["sections"][chord["section"]]["start"]) * 100
                cutoff = min(2600, round(cutoff / 100) * 100)
                # A smooth, syncopated volume gate applied to full voiced chord audio.
                length = min(end - t - .025, self.bar)
                if length > .05:
                    gate_t = np.arange(round(length * self.sr)) / self.sr / self.beat
                    steps = [(0, .42), (.75, .32), (1.25, .35), (2, .60), (2.75, .26), (3.25, .50)]
                    gate = np.full(len(gate_t), .05)
                    for off, dur in steps:
                        u = (gate_t - off) / dur
                        envelope = np.where((u >= 0) & (u <= 1), np.sin(np.pi * np.clip(u, 0, 1)) ** .65, 0)
                        gate = np.maximum(gate, envelope)
                    for pitch in chord["voices"]:
                        voice = air_saw(pitch + 12, length, cutoff) * gate[:, None]
                        self.note("chords", t, length, pitch + 12, .40 if strong else .19,
                                  sound=voice, boundary=b)
                    self.automation.append({"time": t, "duration": length, "stem": "chords", "filter_hz": cutoff,
                                            "amplitude_gate_beats": steps, "gate_floor": .05})
                if strong and bar % 4 != 2:
                    motif = [(0.5, .5, 4), (1.5, .3, 3), (2.5, .6, 1), (3.5, .35, 2)] if bar % 2 == 0 else [(0, .75, 2), (1.25, .55, 1), (2.5, .95, 0)]
                    for off, beats, index in motif:
                        self.pitched("lead", chord, t + off * self.beat, beats * self.beat,
                                     chord["voices"][index] + 12, .27, ribbon, .08)
            if role == "build" and self.cfg["sections"][chord["section"]]["end"] - t <= self.bar * 2 + .01:
                for j in range(8 if bar % 2 == 0 else 16):
                    self.drum(t, j * (0.5 if bar % 2 == 0 else .25), "snare", .20 + j * .012, end, velocity=49 + j * 2)

    def dnb(self, chord):
        a, b, role = chord["start"], chord["end"], chord["role"]
        active, strong = role in ("groove", "build", "drop"), role == "drop"
        self.pad(chord, .055 if active else .11)
        for local in range(math.ceil((b - a) / self.bar)):
            t = a + local * self.bar
            end = min(t + self.bar, b)
            bar = round(t / self.bar)
            if active:
                kicks = [0, 1.75, 2.5] if bar % 2 == 0 else [0, 2.25, 3.5]
                if role == "build":
                    kicks = [0, 2.5]
                for off in kicks:
                    self.drum(t, off, "kick", .87 if strong else .53, end, velocity=106)
                for off in [1, 3]:
                    self.drum(t, off, "snare", 1.12 if strong else .64, end, velocity=110)
                if strong:
                    for off in [.75, 2.75, 3.75 if bar % 4 == 3 else 1.5]:
                        self.drum(t, off, "snare", .16, end, -.12, 39)
                for j in range(8 if not strong else 16):
                    off = j * (0.5 if not strong else .25)
                    self.drum(t, off, "hat", [.34, .23, .62, .28][j % 4], end, (-1) ** j * .23,
                              [48, 36, 72, 42][j % 4])
                if strong:
                    self.drum(t, 2.5, "open", .60, end, .19, 78)
                # Long/short bass calls move around the broken kicks. A separate mono sub carries weight.
                phrase = [(0.25, .95, 0), (1.75, .50, 7), (2.5, .85, 0), (3.5, .35, 12)] if bar % 2 == 0 else [(0, .70, 0), (1.25, .60, 12), (2.25, 1.45, 0)]
                for off, beats, jump in phrase:
                    start, length, pitch = t + off * self.beat, beats * self.beat, chord["root"] + jump
                    self.pitched("bass", chord, start, length, pitch, .49 if strong else .29, sub)
                    cutoff = [1700, 850, 2200, 1250][bar % 4]
                    self.pitched("chords", chord, start, length, pitch, .77 if strong else .31,
                                 reese_mid, cutoff=cutoff)
                    self.automation.append({"time": start, "duration": length, "stem": "chords",
                                            "reese_low_hz": 125, "reese_filter_hz": cutoff, "detune_cents": [-10, 10]})
                if strong and bar % 8 in (0, 4):
                    for off, index in [(1.5, 2), (3.25, 1)]:
                        self.pitched("lead", chord, t + off * self.beat, .25 * self.beat,
                                     chord["voices"][index] + 24, .12, glass, -.13)
                if bar % 8 == 7:
                    for off in [3.25, 3.5, 3.75]:
                        self.drum(t, off, "snare", .38, end, velocity=65)
            elif bar % 2 == 0:
                for j, pitch in enumerate(chord["voices"][1:]):
                    self.pitched("keys", chord, t + j * .75 * self.beat, self.beat, pitch + 12, .17, ins.organ_voice, (-1) ** j * .12)

    def garage(self, chord):
        a, b, role = chord["start"], chord["end"], chord["role"]
        active, strong = role in ("groove", "drop"), role == "drop"
        if role in ("intro", "break", "outro"):
            self.pad(chord, .065)
        for local in range(math.ceil((b - a) / self.bar)):
            t = a + local * self.bar
            end = min(t + self.bar, b)
            bar = round(t / self.bar)
            if active:
                for off in ([0, 2.5] if bar % 2 == 0 else [0, 1.75, 3.25]):
                    self.drum(t, off, "kick", .79 if strong else .58, end, velocity=100)
                for off in [1, 3]:
                    self.drum(t, off, "clap", .95 if strong else .62, end, .05, 94)
                    self.drum(t, off, "rim", .45, end, -.12, 67)
                for j in range(16):
                    if j % 4 == 0 or (j % 4 == 1 and bar % 2 == 0):
                        continue
                    off = j / 4 + (.09 if j % 2 else 0)
                    self.drum(t, off, "hat", .53 if j % 4 == 2 else .31, end, (-1) ** j * .25, 66 if j % 4 == 2 else 43)
                if bar % 2 == 1:
                    self.drum(t, 2.5, "open", .39, end, .15, 61)
                for off in [.84, 2.34, 3.84]:
                    self.drum(t, off, "rim", .45 if strong else .22, end, -.24, 56)
                bass_phrase = [(0, .45, 0), (.84, .30, 12), (1.75, .30, 7), (2.5, .45, 0), (3.34, .32, 12)] if bar % 2 == 0 else [(.34, .48, 0), (1.5, .35, 7), (2.34, .30, 12), (3.25, .42, 0)]
                for off, beats, jump in bass_phrase:
                    self.pitched("bass", chord, t + off * self.beat, beats * self.beat,
                                 chord["root"] + jump, .57 if strong else .38, sub, clipped=True)
            # Tine-key stabs and organ answers use different rhythms and registers.
            key_hits = [(.34, .62), (1.75, .40), (2.84, .65)] if active else [(0, 1.4), (2.34, .85)]
            for off, beats in key_hits:
                for j, pitch in enumerate(chord["voices"]):
                    self.pitched("keys", chord, t + off * self.beat, beats * self.beat, pitch + 12,
                                 .23 if strong else .18, ins.tine_keys, (j - 1.5) * .06)
            if strong and bar % 4 in (1, 3):
                for off, index in [(1.34, 2), (3.34, 0)]:
                    self.pitched("lead", chord, t + off * self.beat, .34 * self.beat,
                                 chord["voices"][index] + 24, .23, ins.organ_voice, -.16)
            self.automation.append({"time": t, "duration": end - t, "groove": "two-step",
                                    "odd_sixteenth_delay_beats": .09, "stem": "drums"})

    def dub(self, chord):
        a, b, role = chord["start"], chord["end"], chord["role"]
        active = role in ("groove", "build", "drop")
        if role in ("intro", "break", "outro"):
            self.pad(chord, .067, octave=0)
        for local in range(math.ceil((b - a) / self.bar)):
            t = a + local * self.bar
            end = min(t + self.bar, b)
            bar = round(t / self.bar)
            if active:
                for off in [0, 1, 2, 3]:
                    self.drum(t, off, "kick", .66 if role == "drop" else .53, end, velocity=93)
                for off in [.5, 1.5, 2.5, 3.5]:
                    self.drum(t, off, "hat", .42 if bar % 4 != 3 else .56, end, .14, 58)
                for off in [1, 3]:
                    self.drum(t, off, "rim", .55, end, -.15, 67)
                if bar % 4 == 3:
                    for off in [2.75, 3.75]:
                        self.drum(t, off, "hat", .31, end, -.22, 46)
                for off, beats in [(.5, .55), (2.5, .60)]:
                    self.pitched("bass", chord, t + off * self.beat, beats * self.beat,
                                 chord["root"], .40, sub)
            elif bar % 2 == 1 and role != "outro":
                self.drum(t, 1.5, "hat", .21, end, .15, 40)
            if bar % 2 == 0 or role == "drop":
                cutoff = round((900 + 1150 * (.5 + .5 * math.sin(t * .09 - 1))) / 50) * 50
                if role == "outro":
                    cutoff = 750
                hits = [.5, 2.75] if role == "drop" and bar % 4 == 2 else [.5]
                for off in hits:
                    start = t + off * self.beat
                    # Three dotted-eighth echoes; each gets darker and quieter.
                    for echo, delay in enumerate([0, .75, 1.5, 2.25]):
                        for pitch in chord["voices"]:
                            self.pitched("chords", chord, start + delay * self.beat,
                                         .8 * self.beat, pitch + 12, .31 * .57 ** echo,
                                         dub_voice, cutoff=max(450, cutoff - echo * 220))
                    self.automation.append({"time": start, "stem": "chords", "filter_hz": cutoff,
                                            "echo_delays_beats": [0, .75, 1.5, 2.25], "echo_gain_ratio": .57,
                                            "echo_filter_loss_hz": 220, "echo_boundary": b})

    def arrange(self):
        method = {"future-bass": self.future, "drum-and-bass": self.dnb,
                  "uk-garage": self.garage, "dub-techno": self.dub}[self.identity]
        for chord in self.harmony:
            method(chord)
        for i, section in enumerate(self.cfg["sections"]):
            start = section["start"]
            if i and section["role"] == "drop" and self.identity != "dub-techno":
                self.add("effects", start, ins.crash(), .30)
                if self.identity == "future-bass":
                    self.add("effects", start - 1.4, ins.swell(1.4), .75)

    def mix(self):
        for name, cutoff in [("keys", 170), ("pad", 250 if self.identity != "dub-techno" else 170),
                             ("chords", 125 if self.identity == "drum-and-bass" else 210),
                             ("lead", 400), ("arp", 500), ("effects", 850)]:
            self.stems[name] = ins.filt(self.stems[name], cutoff)
        self.stems["bass"] = ins.filt(self.stems["bass"], 180 if self.identity == "drum-and-bass" else 240, "lowpass")
        depth, release = {"future-bass": (.64, .22), "drum-and-bass": (.58, .13),
                          "uk-garage": (.52, .14), "dub-techno": (.39, .23)}[self.identity]
        duck = np.ones(self.n, np.float32)
        dt = np.arange(round(release * self.sr)) / self.sr
        env = 1 - depth * np.exp(-dt * (5 / release))
        attack = round(.003 * self.sr)
        env[:attack] = np.linspace(1, env[attack], attack)
        for start in self.kicks:
            k = round(start * self.sr)
            size = min(len(env), self.n - k)
            duck[k:k + size] = np.minimum(duck[k:k + size], env[:size])
        for name, amount in [("bass", 1), ("chords", .75), ("keys", .48), ("pad", .55)]:
            self.stems[name] *= (1 - (1 - duck) * amount)[:, None]
        self.automation.append({"processor": "kick ducking", "kick_onsets_seconds": self.kicks,
                                "depth": depth, "recovery_seconds": release, "attack_seconds": .003,
                                "stem_depth_multipliers": {"bass": 1, "chords": .75, "keys": .48, "pad": .55}})
        audio = sum(self.stems.values())
        fade_in, fade_out = round(.08 * self.sr), round(2.3 * self.sr)
        audio[:fade_in] *= np.sin(np.linspace(0, math.pi / 2, fade_in))[:, None] ** 2
        audio[-fade_out:] *= np.cos(np.linspace(0, math.pi / 2, fade_out))[:, None] ** 2
        peak = float(np.abs(audio).max())
        audio *= .80 / max(.80, peak)
        if not np.isfinite(audio).all():
            raise ValueError("Non-finite mix")
        wavfile.write(self.root / "work/score-mix.wav", self.sr, audio.astype(np.float32))
        (self.root / "work/automation.json").write_text(json.dumps(self.automation, indent=2), encoding="utf-8")

    def audit(self):
        conflicts = []
        for event in self.events:
            if event["stem"] == "drums":
                continue
            for chord in self.harmony:
                if event["time"] < chord["end"] - 1e-7 and event["time"] + event["duration"] > chord["start"] + 1e-7:
                    if event["note"] % 12 not in chord["pcs"]:
                        conflicts.append({"event": event, "chord": chord["name"]})
        if conflicts:
            raise ValueError("Unexpected pitched-note/chord conflicts: " + json.dumps(conflicts[:4]))
        music = self.cfg["music"]
        metadata = {"duration_seconds": self.duration, "bpm": self.bpm, "key": music["key"],
                    "style": music["style"], "identity": self.identity, "sound_design": music["sound_design"],
                    "original_composition": True, "instrument_source": self.instrument_source,
                    "note_events": len(self.events), "unexpected_chord_conflicts": 0,
                    "harmonic_audit": "Explicit root and seventh/ninth chord pitch classes; sounding echoes clipped at harmonic boundaries.",
                    "limits": "Symbolic harmony and signal measurements do not establish listening quality.",
                    "harmony": [{k: v for k, v in c.items() if k != "pcs"} for c in self.harmony]}
        (self.root / "work/note-events.json").write_text(json.dumps(self.events, indent=2), encoding="utf-8")
        (self.root / "work/music-metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        print("MUSIC_AUDIT", json.dumps({k: metadata[k] for k in ["identity", "bpm", "key", "note_events", "unexpected_chord_conflicts"]}), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", type=Path, required=True)
    args = ap.parse_args()
    root, cfg = load(args.project)
    score = Showcase(root, cfg)
    score.arrange()
    score.audit()
    score.mix()
    score.write_midi(root / "outputs" / (cfg["slug"] + "-music.mid"))
    print("NEW_COMPOSITION_COMPLETE", cfg["slug"], flush=True)
