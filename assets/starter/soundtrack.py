"""Import a finished score without loudness processing; preserve its provenance."""
import hashlib
import json
import math
from pathlib import Path
import subprocess

import numpy as np


def import_finished(finisher, audio_path, metadata_path):
    audio_path, metadata_path = Path(audio_path).resolve(), Path(metadata_path).resolve()
    music = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
    if not isinstance(music, dict) or not (
        isinstance(music.get("original_composition"), bool)
        or isinstance(music.get("composition"), str) and music["composition"].strip()
    ):
        raise ValueError("Audio metadata needs original_composition (boolean) or composition (description/rights)")
    master = finisher.work / "score-master.wav"
    if audio_path in (master.resolve(), finisher.bgm.resolve(), finisher.film.resolve()):
        raise ValueError("Use a source audio file outside the destination master/BGM/film paths")
    decoded = subprocess.run([
        finisher.ff, "-v", "error", "-i", str(audio_path), "-map", "0:a:0",
        "-f", "f32le", "-ac", "2", "-ar", "48000", "pipe:1"
    ], capture_output=True)
    if decoded.returncode or decoded.stderr or not decoded.stdout:
        raise ValueError("Cannot decode the supplied soundtrack")
    audio = np.frombuffer(decoded.stdout, dtype="<f4").reshape(-1, 2)
    samples = round(finisher.cfg["duration"] * 48000)
    # Allow only a small codec/resampling boundary, never loop a short track or
    # silently cut a longer arrangement to make it fit the film.
    if abs(len(audio) - samples) > round(.04 * 48000):
        raise ValueError("Soundtrack duration differs from the film by more than 40 ms; revise its arrangement")
    if not np.isfinite(audio).all() or np.abs(audio).max() >= 1:
        raise ValueError("Supplied soundtrack contains invalid or clipped samples; revise its master")
    finisher.run([
        "-y", "-i", str(audio_path), "-map", "0:a:0",
        "-af", f"aresample=48000,apad,atrim=end_sample={samples}",
        "-ac", "2", "-c:a", "pcm_s24le", str(master)
    ], "soundtrack-import.log")
    finisher.encode_bgm()
    with audio_path.open("rb") as source:
        audio_hash = hashlib.file_digest(source, "sha256").hexdigest()
    provenance = {
        "mode": "finished-audio-import", "source_file": audio_path.name,
        "source_sha256": audio_hash, "metadata_file": metadata_path.name,
        "metadata_sha256": hashlib.sha256(metadata_path.read_bytes()).hexdigest(),
        "source_metadata": music, "decoded_source_samples_48k": len(audio),
        "output_samples_48k": samples, "boundary_adjustment_samples": samples - len(audio),
        "processing": "48kHz stereo PCM conversion, <=40ms boundary trim/pad, AAC encoding; no gain/EQ/limiting/loudness normalization"
    }
    (finisher.work / "soundtrack-import.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Copy all supplied fields, including free-time descriptions and licenses.
    # The complete original object is also kept inside the import record.
    (finisher.work / "music-metadata.json").write_text(
        json.dumps({**music, "audio_import": provenance}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print("FINISHED_SOUNDTRACK_IMPORTED", flush=True)


def silence_regions(audio, sr, duration, intentional):
    """Return one-second near-silent regions, accounting for declared rests.

    A rest must cover the whole analysis window; overlap alone cannot hide an
    unexpected gap. Edge windows retain the starter's fade allowance.
    """
    if not isinstance(intentional, list):
        raise ValueError("music.intentional_silence must be a list of [start, end] seconds")
    for interval in intentional:
        if not isinstance(interval, (list, tuple)) or len(interval) != 2 or any(
            isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in interval
        ) or not 0 <= interval[0] < interval[1] <= duration:
            raise ValueError("Invalid music.intentional_silence interval")
    bins = [(k / sr, min((k + sr) / sr, duration), float(np.sqrt(np.mean(audio[k:k + sr] ** 2))))
            for k in range(0, min(len(audio), round(duration * sr)), sr)]
    interior = bins[1:-2] if len(bins) >= 5 else bins[:-1]
    quiet = [{"start": a, "end": b, "rms": rms,
              "intentional": any(x <= a + 1e-9 and y >= b - 1e-9 for x, y in intentional)}
             for a, b, rms in interior if rms < .0005]
    return quiet
