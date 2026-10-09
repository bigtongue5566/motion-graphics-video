"""Download the exact piano SoundFont and license in sources.json and verify SHA-256."""
import hashlib
import json
from pathlib import Path
import urllib.request


def main():
    root = Path(__file__).resolve().parent
    records = json.loads((root / "sources.json").read_text(encoding="utf-8"))["sampled_instruments"]
    assets = root / "work/assets"
    assets.mkdir(parents=True, exist_ok=True)
    for record in records:
        name = record["file"]
        if Path(name).name != name:
            raise ValueError("Instrument record must contain a plain filename")
        path = assets / name
        if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]:
            print("VERIFIED", name)
            continue
        if path.exists():
            raise ValueError("Preserve existing file with a different hash: " + name)
        request = urllib.request.Request(record["url"], headers={"User-Agent": "tsmc-piano-reproduction"})
        with urllib.request.urlopen(request, timeout=60) as response:
            content = response.read()
        if hashlib.sha256(content).hexdigest() != record["sha256"]:
            raise ValueError("Downloaded instrument differs from the published source record: " + name)
        path.write_bytes(content)
        print("DOWNLOADED_AND_VERIFIED", name)


if __name__ == "__main__":
    main()
