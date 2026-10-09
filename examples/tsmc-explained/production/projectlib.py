"""Music-only configuration, diatonic harmony, and shared section timing."""
import json
import math
from pathlib import Path
import re

ROLES = {"intro", "groove", "build", "drop", "break", "outro"}
PITCH = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
MAJOR = {
    "I": ([55, 59, 62], 43, [71, 74, 79, 74]),
    "ii": ([57, 60, 64], 45, [72, 76, 81, 76]),
    "iii": ([54, 59, 62], 47, [71, 74, 78, 74]),
    "IV": ([55, 60, 64], 36, [67, 72, 76, 72]),
    "V": ([54, 57, 62], 38, [69, 74, 78, 74]),
    "vi": ([55, 59, 64], 40, [71, 76, 79, 76]),
}
MINOR = {
    "i": ([57, 60, 64], 45, [72, 76, 81, 76]),
    "III": ([55, 60, 64], 36, [67, 72, 76, 72]),
    "iv": ([57, 62, 65], 38, [69, 74, 77, 74]),
    "v": ([55, 59, 64], 40, [71, 76, 79, 76]),
    "V": ([56, 59, 64], 40, [71, 76, 80, 76]),
    "VI": ([57, 60, 65], 41, [72, 77, 81, 77]),
    "VII": ([55, 59, 62], 43, [71, 74, 79, 74]),
}


def normalize_key(key):
    match = re.fullmatch(r"([A-Ga-g])([#b]?)\s+(major|minor)", str(key).strip(), re.I)
    if not match:
        raise ValueError("music.key must use a note and major/minor, such as G major or A minor")
    letter, accidental, mode = match.groups()
    pc = (PITCH[letter.upper()] + (1 if accidental == "#" else -1 if accidental == "b" else 0)) % 12
    names = (["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"] if mode.lower() == "major"
             else ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])
    return names[pc] + " " + mode.lower(), pc


def harmonic_material(key):
    canonical, pc = normalize_key(key)
    minor = canonical.endswith("minor")
    return (MINOR if minor else MAJOR), ((pc - (9 if minor else 7) + 6) % 12 - 6)


def validate(cfg):
    if not isinstance(cfg.get("name"), str) or not cfg["name"].strip():
        raise ValueError("name must be nonempty text")
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", str(cfg.get("slug", ""))):
        raise ValueError("slug must use letters, numbers, underscore or hyphen")
    duration = float(cfg["duration"])
    if not math.isfinite(duration) or duration < 1:
        raise ValueError("duration must be a finite number of seconds, at least one")
    if abs(duration * 48000 - round(duration * 48000)) > 1e-4:
        raise ValueError("duration must correspond to an integer number of 48kHz samples")
    music = cfg["music"]
    bpm = float(music["bpm"])
    if not math.isfinite(bpm) or not 30 <= bpm <= 240:
        raise ValueError("This starter supports 30–240 BPM; adapt note lengths for other tempos")
    music["key"], _ = normalize_key(music["key"])
    data, _ = harmonic_material(music["key"])
    progression = music["progression"]
    if not isinstance(progression, list) or not progression or any(degree not in data for degree in progression):
        raise ValueError("Use supported progression degrees for this key mode: " + ", ".join(data))
    for field, bounds in [("lufs", (-35, -7)), ("true_peak", (-12, -.3))]:
        number = float(music[field])
        if not math.isfinite(number) or not bounds[0] <= number <= bounds[1]:
            raise ValueError(f"music.{field} must be within {bounds}")
    if not isinstance(music.get("seed", 19712026), int):
        raise ValueError("music.seed must be an integer")
    if not isinstance(music.get("export_stems", False), bool):
        raise ValueError("music.export_stems must be true or false")
    sections = cfg["sections"]
    if not isinstance(sections, list) or not sections:
        raise ValueError("At least one section is required")
    previous = 0.
    for section in sections:
        a, b = float(section["start"]), float(section["end"])
        if not math.isfinite(a) or not math.isfinite(b) or abs(a - previous) > 1e-7 or b <= a:
            raise ValueError("Section times must be finite, positive, contiguous and start at zero")
        if section["role"] not in ROLES:
            raise ValueError("Unknown section role")
        previous = b
    if abs(previous - duration) > 1e-7:
        raise ValueError("Sections must cover the requested duration exactly")
    return cfg


def load(project):
    root = Path(project).resolve()
    cfg = validate(json.loads((root / "project.json").read_text(encoding="utf-8-sig")))
    for folder in ("work", "outputs"):
        (root / folder).mkdir(exist_ok=True)
    return root, cfg


def local_path(root, value):
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else root / path


def section_at(cfg, time):
    for index, section in enumerate(cfg["sections"]):
        if time < section["end"]:
            return index, section
    return len(cfg["sections"]) - 1, cfg["sections"][-1]
