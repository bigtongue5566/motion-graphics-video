"""Band-limited melodic-house instrument and percussion primitives."""
from functools import lru_cache
import math
import numpy as np
from scipy.signal import butter, sosfilt

SR = 48000
RNG = np.random.default_rng(19712026)

def hz(note):
    return 440. * 2. ** ((note - 69) / 12.)


def filt(sound, cutoff, kind="highpass", order=2):
    return sosfilt(butter(order, cutoff, btype=kind, fs=SR, output="sos"), sound, axis=0).astype(np.float32)


def soften(sound, attack=.008, release=.075):
    sound = np.array(sound, np.float32, copy=True)
    a = min(len(sound), max(1, round(attack * SR)))
    r = min(len(sound), max(1, round(release * SR)))
    sound[:a] *= np.sin(np.linspace(0, math.pi / 2, a)) ** 2
    sound[-r:] *= np.cos(np.linspace(0, math.pi / 2, r)) ** 2
    return sound


def release_shape(sound, gate, attack, release):
    """MIDI note-off begins release; it does not terminate the waveform."""
    sound = np.array(sound, np.float32, copy=True)
    t = np.arange(len(sound))/SR
    envelope = np.sin(np.clip(t/max(attack,1/SR),0,1)*math.pi/2)**2
    envelope *= np.cos(np.clip((t-gate)/release,0,1)*math.pi/2)**2
    return sound*envelope


@lru_cache(maxsize=256)
def pluck(note, duration, brightness=2100.):
    """Band-limited, softly filtered saw/triangle pluck; no metallic FM."""
    t = np.arange(round((duration + 0.24) * SR), dtype=np.float64) / SR
    f = hz(note)
    env = (1 - np.exp(-t * 220)) * np.exp(-t * 5.0)
    sig = np.zeros_like(t)
    # All partials are exact integer harmonics. The high frequencies decay faster.
    for h in range(1, min(64, int(18000 // f)) + 1):
        harmonic_filter = 1 / math.sqrt(1 + (h * f / brightness) ** 6)
        coeff = harmonic_filter / h ** 1.45
        sig += coeff * np.sin(2 * math.pi * f * h * t + .18 * h) * np.exp(-t * .12 * h)
    return release_shape(sig * env * .54, duration, .006, 0.24)


@lru_cache(maxsize=256)
def chord_voice(note, duration=.31, bright=False):
    """Gentle stereo detuning, tightly voiced chords, rounded attack."""
    t = np.arange(round((duration + 0.22) * SR), dtype=np.float64) / SR
    f = hz(note)
    stereo = np.zeros((len(t), 2), dtype=np.float64)
    cutoff = 2300. if bright else 1250.
    env = np.minimum(t / .015, 1.) * np.exp(-t * 2.4)
    for channel, cents in [(0, -4.), (1, 4.)]:
        detune = 2 ** (cents / 1200.)
        for h in range(1, min(42, int(16000 // f)) + 1):
            coeff = 1 / h ** 1.35 / math.sqrt(1 + (h * f / cutoff) ** 6)
            stereo[:, channel] += coeff * np.sin(2 * math.pi * f * detune * h * t + h * .43)
    stereo *= env[:, None] * .26
    for c in range(2):
        stereo[:, c] = release_shape(stereo[:, c], duration, .015, 0.22)
    return stereo.astype(np.float32)


@lru_cache(maxsize=80)
def pad_voice(note, duration):
    t = np.arange(round((duration + 0.3) * SR), dtype=np.float64) / SR
    stereo = np.zeros((len(t), 2), dtype=np.float64)
    f = hz(note)
    for channel, cents in [(0, -2.5), (1, 2.5)]:
        for h, strength in [(1, .58), (2, .17), (3, .07), (4, .028)]:
            stereo[:, channel] += strength * np.sin(2 * math.pi * f * 2 ** (cents / 1200.) * h * t + h * .25)
        stereo[:, channel] = release_shape(stereo[:, channel], duration, min(.16, duration / 4), 0.3)
    stereo *= (.93 + .07 * np.sin(2 * math.pi * .18 * t))[:, None]
    return stereo.astype(np.float32)


@lru_cache(maxsize=96)
def bass_note(note, duration):
    t = np.arange(round((duration + 0.12) * SR), dtype=np.float64) / SR
    f = hz(note)
    sig = .78 * np.sin(2 * math.pi * f * t)
    sig += .22 * np.sin(2 * math.pi * 2 * f * t) + .07 * np.sin(2 * math.pi * 3 * f * t)
    sig *= (1 - np.exp(-t * 180)) * np.exp(-t * 1.65)
    return release_shape(sig * .58, duration, .008, 0.12)


def kick():
    t = np.arange(round(.39 * SR), dtype=np.float64) / SR
    frequency = 50 + 110 * np.exp(-t * 43)
    phase = 2 * math.pi * np.cumsum(frequency) / SR
    body = np.sin(phase) * np.exp(-t * 11)
    punch = .24 * np.sin(phase * 2) * np.exp(-t * 45)
    click = filt(RNG.standard_normal(len(t)).astype(np.float32), [1500, 8000], "bandpass") * np.exp(-t * 170) * .055
    return soften(np.tanh((body + punch + click) * 1.08) * .88, .0007, .045)


def clap():
    t = np.arange(round(.19 * SR), dtype=np.float64) / SR
    noise = filt(RNG.standard_normal(len(t)).astype(np.float32), [1150, 6500], "bandpass")
    env = np.exp(-t * 32) * .68
    for delay in [0., .009, .018]:
        env += np.where(t >= delay, np.exp(-np.maximum(t - delay, 0) * 270), 0) * .45
    return soften(noise * env * .23, .001, .05)


def hat(opened=False):
    dur = .19 if opened else .074
    t = np.arange(round(dur * SR), dtype=np.float64) / SR
    noise = filt(RNG.standard_normal(len(t)).astype(np.float32), [6500, 14500], "bandpass")
    return soften(noise * np.exp(-t * (24 if opened else 62)) * .16, .0008, .025)


def swell(duration):
    t = np.arange(round(duration * SR), dtype=np.float64) / SR
    noise = filt(RNG.standard_normal(len(t)).astype(np.float32), [2200, 8500], "bandpass")
    env = (t / duration) ** 2 * np.minimum((duration - t) / .09, 1)
    return soften(noise * env * .045, .12, .06)


def crash():
    t = np.arange(round(1.55 * SR), dtype=np.float64) / SR
    noise = filt(RNG.standard_normal(len(t)).astype(np.float32), [4500, 13500], "bandpass")
    return soften(noise * np.exp(-t * 4.5) * .065, .002, .2)


@lru_cache(maxsize=256)
def tine_keys(note, duration):
    t = np.arange(round((duration + 0.26) * SR)) / SR
    f = hz(note)
    # Integer-ratio modulation and damped partials; independently synthesized, no samples.
    body = np.sin(2 * math.pi * f * t + .65 * np.exp(-t * 5) * np.sin(2 * math.pi * 2 * f * t))
    body += .12 * np.sin(2 * math.pi * 3 * f * t) * np.exp(-t * 8)
    return release_shape(body * np.exp(-t * 3.2) * .43, duration, .008, 0.26)


@lru_cache(maxsize=256)
def organ_voice(note, duration):
    t = np.arange(round((duration + 0.2) * SR)) / SR
    f = hz(note)
    body = sum(weight * np.sin(2 * math.pi * f * h * t) for h, weight in [(1, .65), (2, .20), (4, .08)] if f * h < 16000)
    return release_shape(body * .42, duration, min(.045, duration / 4), 0.2)


@lru_cache(maxsize=128)
def reese_voice(note, duration):
    t = np.arange(round((duration + 0.12) * SR)) / SR
    f = hz(note)
    body = .65 * np.sin(2 * math.pi * f * t)
    for detune in [2 ** (-6 / 1200), 2 ** (6 / 1200)]:
        for h in [2, 3, 4, 5]:
            body += .20 / h * np.sin(2 * math.pi * f * detune * h * t)
    body = np.tanh(body * 1.6) * (.85 + .15 * np.sin(2 * math.pi * 1.1 * t)) * .40
    return release_shape(body, duration, .012, 0.12)


def tight_kick(fast=False):
    t = np.arange(round((.17 if fast else .24) * SR)) / SR
    phase = 2 * math.pi * np.cumsum(53 + 145 * np.exp(-t * 65)) / SR
    return soften(np.sin(phase) * np.exp(-t * (22 if fast else 16)) * .82, .0008, .025)


def snare(fast=False):
    t = np.arange(round((.14 if fast else .21) * SR)) / SR
    noise = filt(RNG.standard_normal(len(t)).astype(np.float32), [1000, 8500], "bandpass")
    body = .25 * np.sin(2 * math.pi * 185 * t) * np.exp(-t * 27)
    return soften((body + noise * .30 * np.exp(-t * (30 if fast else 22))), .001, .035)
