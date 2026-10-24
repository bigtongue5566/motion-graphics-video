"""Exercise real audio import/mux and guard against changing a finished score."""
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

import imageio_ffmpeg
import numpy as np
from scipy.io import wavfile

REPO = Path(__file__).resolve().parents[1]
STARTER = REPO / "assets" / "starter"
sys.path.insert(0, str(STARTER))
from finish_video import Finisher
from projectlib import load
from soundtrack import import_finished, silence_regions


class SoundtrackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "film"
        subprocess.run([sys.executable, str(REPO / "scripts" / "init_project.py"),
                        "--project", str(self.root), "--duration", "3.3", "--fps", "10",
                        "--size", "160x90"], check=True, capture_output=True)
        cfg = json.loads((self.root / "project.json").read_text(encoding="utf-8"))
        cfg["scenes"] = [{**cfg["scenes"][0], "start": 0, "end": 3.3}]
        (self.root / "project.json").write_text(json.dumps(cfg), encoding="utf-8")
        self.root, self.cfg = load(self.root)
        self.finisher = Finisher(self.root, self.cfg)
        self.audio = self.root / "finished.wav"
        self.metadata = self.root / "source.json"
        self.metadata.write_text(json.dumps({"composition": "Licensed test fixture; test rights record",
                                            "style": "ambient", "pulse": "free",
                                            "license": {"author": "test", "terms": "fixture only"}}), encoding="utf-8")
        t = np.arange(round(3.3 * 48000)) / 48000
        mono = .12 * np.sin(2 * np.pi * 440 * t)
        mono[:2400] *= np.linspace(0, 1, 2400)
        mono[-12000:] *= np.linspace(1, 0, 12000)
        self.signal = np.column_stack([mono, mono]).astype(np.float32)
        wavfile.write(self.audio, 48000, self.signal)

    def packet_hash(self, path):
        return subprocess.run([self.finisher.ff, "-v", "error", "-i", str(path),
                               "-map", "0:v:0", "-c", "copy", "-f", "hash", "-"],
                              check=True, capture_output=True).stdout

    def test_import_mux_preserves_gain_video_and_rights(self):
        self.assertTrue((self.root / "work" / "pyproject.toml").exists())
        subprocess.run([self.finisher.ff, "-v", "error", "-y", "-f", "lavfi", "-i",
                        "color=c=blue:s=160x90:r=10:d=3.3", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        str(self.root / "work" / "picture.mp4")], check=True, capture_output=True)
        measured = subprocess.run([self.finisher.ff, "-hide_banner", "-i", str(self.audio),
                                   "-af", "ebur128=peak=true", "-f", "null", "-"],
                                  check=True, capture_output=True, text=True).stderr
        self.cfg["music"]["lufs"] = float(re.search(r"I:\s*([-\d.]+) LUFS", measured[measured.rfind("Summary:"):]).group(1))
        (self.root / "project.json").write_text(json.dumps(self.cfg), encoding="utf-8")
        subprocess.run([sys.executable, str(self.root / "work" / "finish_video.py"),
                        "--project", str(self.root), "--audio", str(self.audio),
                        "--audio-metadata", str(self.metadata)], check=True, capture_output=True)
        rate, converted = wavfile.read(self.root / "work" / "score-master.wav")
        self.assertEqual(rate, 48000)
        self.assertEqual(converted.shape, self.signal.shape)
        np.testing.assert_allclose(converted.astype(np.float64) / 2**31, self.signal, atol=2e-7)
        self.assertEqual(self.packet_hash(self.root / "work" / "picture.mp4"), self.packet_hash(self.finisher.film))
        self.assertFalse((self.root / "work" / "mastering.log").exists())
        qc = json.loads((self.root / "outputs" / f"{self.cfg['slug']}-qc.json").read_text())
        self.assertEqual(qc["decoded_frames"], 33)
        self.assertEqual(qc["audio_processing"], "finished-audio-import")
        self.assertEqual(qc["micro_dynamics"]["regions"], [])
        source = json.loads((self.root / "outputs" / f"{self.cfg['slug']}-soundtrack-source.json").read_text())
        self.assertEqual(source["source_metadata"]["license"]["author"], "test")
        self.assertEqual(source["boundary_adjustment_samples"], 0)
        note = (self.root / "outputs" / f"{self.cfg['slug']}-production.md").read_text(encoding="utf-8-sig")
        self.assertIn("自由時間", note)
        self.assertNotIn("原創 EDM", note)
        self.assertNotIn("BPM", note)

    def test_wrong_duration_rejected_before_media_is_written(self):
        wavfile.write(self.audio, 48000, self.signal[:48000])
        with self.assertRaisesRegex(ValueError, "duration differs"):
            import_finished(self.finisher, self.audio, self.metadata)
        self.assertFalse(self.finisher.bgm.exists())
        self.assertFalse((self.root / "work" / "score-master.wav").exists())

    def test_missing_provenance_and_unpaired_cli_arguments_rejected(self):
        self.metadata.write_text("{}")
        with self.assertRaisesRegex(ValueError, "metadata needs"):
            import_finished(self.finisher, self.audio, self.metadata)
        result = subprocess.run([sys.executable, str(STARTER / "finish_video.py"),
                                 "--project", str(self.root), "--audio", str(self.audio)], capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"must be supplied together", result.stderr)

    def test_declared_rest_must_cover_the_whole_quiet_window(self):
        sound = np.ones((6 * 48000, 2), np.float32) * .1
        sound[2 * 48000:3 * 48000] = 0
        self.assertFalse(silence_regions(sound, 48000, 6, [])[0]["intentional"])
        self.assertTrue(silence_regions(sound, 48000, 6, [[2, 3]])[0]["intentional"])
        self.assertFalse(silence_regions(sound, 48000, 6, [[2, 2.5]])[0]["intentional"])
        with self.assertRaises(ValueError):
            silence_regions(sound, 48000, 6, [[2, 7]])

    def test_existing_starter_master_path(self):
        wavfile.write(self.root / "work" / "score-mix.wav", 48000, self.signal)
        self.finisher.master()
        self.assertTrue(self.finisher.bgm.exists())
        self.assertTrue((self.root / "work" / "mastering.log").exists())


if __name__ == "__main__":
    unittest.main()
