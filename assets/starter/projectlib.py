"""Shared timing and configuration for animation, score and encoded QC."""
import json
from pathlib import Path
import re


def load(project):
    root = Path(project).resolve()
    cfg = json.loads((root / "project.json").read_text(encoding="utf-8-sig"))
    duration, fps = float(cfg["duration"]), float(cfg["fps"])
    if duration <= 0 or fps <= 0 or abs(duration * fps - round(duration * fps)) > 1e-4:
        raise ValueError("Use a positive duration and fps with an integer number of video frames")
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", cfg["slug"]):
        raise ValueError("slug must use letters, numbers, underscore or hyphen")
    for key in ("width", "height"):
        if not isinstance(cfg[key], int) or cfg[key] <= 0 or cfg[key] % 2:
            raise ValueError(f"{key} must be a positive even integer for H.264 yuv420p")
    for key in ("primary", "secondary", "accent", "ink"):
        if not re.fullmatch(r"#[a-fA-F0-9]{6}", cfg["brand"][key]):
            raise ValueError(f"brand.{key} must use #RRGGBB")
    if not cfg["scenes"]:
        raise ValueError("At least one scene is required")
    previous = 0.
    for scene in cfg["scenes"]:
        if abs(scene["start"] - previous) > 1e-6 or scene["end"] <= scene["start"]:
            raise ValueError("Scene intervals must be positive, contiguous and start at zero")
        if scene["music_role"] not in ["intro", "groove", "build", "drop", "break", "outro"]:
            raise ValueError("Unknown music_role")
        previous = scene["end"]
    if abs(previous - duration) > 1e-6:
        raise ValueError("Scenes must cover the requested duration exactly")
    if float(cfg["music"]["bpm"]) <= 0:
        raise ValueError("music.bpm must be positive")
    for folder in ("work", "outputs"):
        (root / folder).mkdir(exist_ok=True)
    return root, cfg


def local_path(root, value):
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else root / path


def scene_at(cfg, time):
    for index, scene in enumerate(cfg["scenes"]):
        if time < scene["end"]:
            return index, scene
    return len(cfg["scenes"]) - 1, cfg["scenes"][-1]
