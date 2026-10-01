"""Create a self-contained motion/EDM project without overwriting files."""
import argparse
import json
from pathlib import Path
import shutil


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", type=Path, required=True)
    ap.add_argument("--duration", type=float)
    ap.add_argument("--bpm", type=float)
    ap.add_argument("--name")
    ap.add_argument("--size", help="For example 1280x720; starter layout uses 16:9")
    ap.add_argument("--fps", type=float)
    args = ap.parse_args()
    source = Path(__file__).resolve().parents[1] / "assets" / "starter"
    target = args.project.resolve()
    config = json.loads((source / "project.json").read_text(encoding="utf-8"))
    if args.duration is not None:
        if args.duration <= 0:
            ap.error("--duration must be positive")
        scale = args.duration / config["duration"]
        for scene in config["scenes"]:
            scene["start"] *= scale
            scene["end"] *= scale
        config["duration"] = args.duration
        config["scenes"][-1]["end"] = args.duration
    if args.bpm is not None:
        if args.bpm <= 0:
            ap.error("--bpm must be positive")
        config["music"]["bpm"] = args.bpm
    if args.fps is not None:
        config["fps"] = args.fps
    if args.name:
        config["name"] = args.name
        config["brand"]["name"] = args.name
    if args.size:
        try:
            config["width"], config["height"] = [int(x) for x in args.size.lower().split("x")]
        except ValueError:
            ap.error("--size must use WIDTHxHEIGHT")
    files = [p for p in source.iterdir() if p.is_file() and p.name != "project.json"]
    destinations = [target / "project.json"] + [target / "work" / p.name for p in files]
    conflicts = [str(p) for p in destinations if p.exists()]
    if conflicts:
        ap.error("Existing files would be overwritten: " + ", ".join(conflicts))
    (target / "work" / "assets").mkdir(parents=True, exist_ok=True)
    (target / "outputs").mkdir(exist_ok=True)
    for file in files:
        shutil.copy2(file, target / "work" / file.name)
    (target / "project.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PROJECT_CREATED {target}")


if __name__ == "__main__":
    main()
