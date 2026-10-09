"""Original, audio-reactive geometric film. No stock images or company identities."""
import argparse
from bisect import bisect_right
from functools import lru_cache
import json
import math
from pathlib import Path
import subprocess

import imageio_ffmpeg
import numpy as np
from PIL import Image
from scipy.io import wavfile
import skia


def ease(x):
    x = max(0., min(1., x))
    return x * x * (3 - 2 * x)


def color(value, alpha=1.):
    value = value.lstrip("#")
    return skia.ColorSetARGB(round(255 * max(0., min(1., alpha))), *[int(value[i:i + 2], 16) for i in (0, 2, 4)])


def paint(value, alpha=1., width=None):
    p = skia.Paint(Color=color(value, alpha), AntiAlias=True)
    if width is not None:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(width)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


class Film:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.cfg = json.loads((self.root / "project.json").read_text(encoding="utf-8"))
        video = self.cfg["video"]
        self.w, self.h, self.fps = video["width"], video["height"], video["fps"]
        self.duration, self.palette = self.cfg["duration"], video["palette"]
        self.scenes = video["scenes"]
        self.beat = 60 / self.cfg["music"]["bpm"]
        events = json.loads((self.root / 'work/note-events.json').read_text(encoding='utf-8'))
        self.kick_times = sorted(e['time'] for e in events if e['stem'] == 'drums' and e['note'] == 36)
        self.surface = skia.Surface.MakeRaster(skia.ImageInfo.Make(self.w, self.h,
                       skia.ColorType.kRGBA_8888_ColorType, skia.AlphaType.kPremul_AlphaType))
        self.faces = {}
        for language, path in video["fonts"].items():
            face = skia.Typeface.MakeFromFile(str(self.root / path))
            if face is None:
                raise ValueError("Cannot load the licensed font: " + path)
            self.faces[language] = face
        needed = "".join(str(scene[field]) for scene in self.scenes for field in ("headline", "body", "caption"))
        for char in set(needed):
            if "\u3400" <= char <= "\u9fff" and self.faces["cn"].unicharToGlyph(ord(char)) == 0:
                raise ValueError("Missing Chinese glyph: " + char)
        self.backgrounds = {light: self.background(light) for light in (False, True)}
        rate, audio = wavfile.read(self.root / "outputs" / (self.cfg["slug"] + "-master.wav"))
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32) / np.iinfo(audio.dtype).max
        mono = audio.mean(axis=1)
        self.levels, self.spectra = [], []
        edges = np.geomspace(65, 6500, 33)
        frequencies = np.fft.rfftfreq(4096, 1 / rate)
        for frame in range(round(self.duration * self.fps)):
            k = round(frame / self.fps * rate)
            window = np.zeros(4096)
            part = mono[k:k + 4096]
            window[:len(part)] = part
            self.levels.append(float(np.sqrt(np.mean(window ** 2))))
            spectrum = np.abs(np.fft.rfft(window * np.hanning(4096)))
            bins = [float(np.sqrt(np.mean(spectrum[(frequencies >= a) & (frequencies < b)] ** 2)))
                    for a, b in zip(edges[:-1], edges[1:])]
            self.spectra.append(bins)
        self.levels = np.asarray(self.levels)
        self.levels /= max(1e-6, np.quantile(self.levels, .98))
        self.spectra = np.log1p(np.asarray(self.spectra))
        self.spectra /= np.maximum(.1, np.quantile(self.spectra, .98, axis=0))
        self.spectra = np.clip(self.spectra, 0, 1)
        self.frequencies = frequencies
        self.angles = np.linspace(0, 2 * math.pi, 361)
        self.cube_vertices = np.array([[-1,-1,-1], [1,-1,-1], [1,1,-1], [-1,1,-1],
                                      [-1,-1,1], [1,-1,1], [1,1,1], [-1,1,1]], dtype=float)
        self.cube_faces = [[0,1,2,3], [4,5,6,7], [0,4,7,3], [1,5,6,2], [0,1,5,4], [3,2,6,7]]

    def pulse_at(self, time):
        index = bisect_right(self.kick_times, time) - 1
        return math.exp(-(time - self.kick_times[index]) / .13) if index >= 0 else 0.

    @lru_cache(maxsize=160)
    def font(self, size, language="en", bold=False):
        f = skia.Font(self.faces[language], size)
        f.setEdging(skia.Font.Edging.kAntiAlias)
        f.setSubpixel(True)
        f.setEmbolden(bold)
        return f

    def text(self, c, text, x, y, size, value, alpha=1., center=False, width=None, bold=False):
        for row, line in enumerate(str(text).splitlines()):
            language = "cn" if any("\u3400" <= char <= "\u9fff" for char in line) else "en"
            f = self.font(size, language, bold)
            measured = f.measureText(line)
            if width and measured > width:
                f = self.font(size * width / measured, language, bold)
                measured = f.measureText(line)
            c.drawString(line, x - measured / 2 if center else x, y + row * size * 1.22, f, paint(value, alpha))

    def path(self, c, pts, value, alpha=1., stroke=2., closed=False, fill=False):
        if len(pts) < 2:
            return
        p = skia.Path()
        p.moveTo(float(pts[0][0]), float(pts[0][1]))
        for x, y in pts[1:]:
            p.lineTo(float(x), float(y))
        if closed:
            p.close()
        c.drawPath(p, paint(value, alpha, None if fill else stroke))

    def background(self, light):
        surface = skia.Surface(self.w, self.h)
        c = surface.getCanvas()
        a, b = ("#F2F2EA", "#E5E9E4") if light else ("#080C16", "#111C2B")
        p = paint(a)
        p.setShader(skia.GradientShader.MakeLinear([(0, 0), (self.w, self.h)], [color(a), color(b)]))
        c.drawRect(skia.Rect.MakeWH(self.w, self.h), p)
        grid = "#192A35" if light else "#C2DCD1"
        for x in range(104, 1820, 120):
            for y in range(164, 930, 120):
                c.drawCircle(x, y, 1.05, paint(grid, .13 if light else .085))
        return surface.makeImageSnapshot()

    def projection(self, pts, t, cx=1425, cy=540, scale=1.):
        yaw, pitch = -.64 + .14 * math.sin(t * .15), .44 + .07 * math.cos(t * .11)
        ry = np.array([[math.cos(yaw), 0, math.sin(yaw)], [0, 1, 0], [-math.sin(yaw), 0, math.cos(yaw)]])
        rx = np.array([[1,0,0], [0,math.cos(pitch),-math.sin(pitch)], [0,math.sin(pitch),math.cos(pitch)]])
        q = np.asarray(pts) @ ry.T @ rx.T
        perspective = 1100 / (1100 - q[:, 2])
        return np.column_stack([cx + q[:, 0] * perspective * scale, cy - q[:, 1] * perspective * scale]), q[:, 2]

    def torus(self, c, t, level, pulse, cx=1425, cy=545, scale=1.):
        u = self.angles
        radius = 215 + 70 * np.cos(3 * u + t * .18)
        xyz = np.column_stack([radius * np.cos(2 * u), radius * np.sin(2 * u), 95 * np.sin(3 * u + t * .18)])
        phase = t * .12
        spin = np.array([[math.cos(phase), -math.sin(phase), 0], [math.sin(phase), math.cos(phase), 0], [0,0,1]])
        xy, _ = self.projection(xyz @ spin.T, t, cx, cy, scale * (1 + .035 * pulse + .035 * level))
        self.path(c, xy, "#61E6C4", .11, 15.)
        for j in range(12):
            self.path(c, xy[j * 30:(j + 1) * 30 + 1], "#FF6672" if j % 4 == 0 else "#61E6C4", .94, 3.2)
        for j in range(0, 360, 30):
            x, y = xy[(j + round(t * 14)) % 360]
            c.drawCircle(float(x), float(y), 4.5 + level * 2, paint("#F2F2EA", .95))
        c.drawCircle(cx, cy, 5 + pulse * 6, paint("#FF6672", .9))

    def cubes(self, c, t, u, level, pulse, assembling=False):
        objects = []
        formation = ease(u / 5) if assembling else 1.
        for row in range(3):
            for col in range(3):
                index = row * 3 + col
                center = np.array([(row - 1) * 172, 50 * math.sin(index * .7 + t * .9) + pulse * 34, (col - 1) * 172])
                if assembling:
                    center += (1 - formation) * np.array([120 * math.sin(index * 2), 180 * math.cos(index), 170 * math.sin(index)])
                size = 48 + 11 * level + 3 * math.sin(t + index)
                xyz = self.cube_vertices * size + center
                points, depth = self.projection(xyz, t, scale=1.18)
                objects.append((depth.mean(), points, depth, index))
        for _, points, depth, index in sorted(objects, key=lambda item: item[0]):
            for face in sorted(self.cube_faces, key=lambda indices: float(depth[indices].mean())):
                tone = "#FF6672" if index in (2, 6) else "#61E6C4"
                opacity = .17 + .055 * (face == self.cube_faces[-1])
                self.path(c, points[face], tone, opacity, closed=True, fill=True)
                self.path(c, points[face], tone, .83, 1.65, closed=True)
        self.text(c, "FORM / 03 × 03", 1425, 905, 18, "#90A4A4", .75, center=True)

    def waves(self, c, t, level):
        x = np.linspace(965, 1815, 180)
        z = np.linspace(0, 2 * math.pi, len(x))
        for j in range(11):
            y = 520 + (j - 5) * 22 + (140 + 65 * level) * np.sin(z * .85 - t * .72 + j * .13)
            y += 25 * np.sin(z * 1.65 + t * .35)
            tone = "#FB626F" if j in (4, 5) else "#52756C"
            self.path(c, np.column_stack([x, y]), tone, .85 if j in (4, 5) else .27, 3 if j == 5 else 1.5)

    def network(self, c, t, u, level, pulse):
        ids = np.arange(31)
        theta = ids * 2.39996323 + t * .04
        radius = np.sqrt(ids / 30) * (310 + level * 28)
        xyz = np.column_stack([radius * np.cos(theta), radius * np.sin(theta), 60 * np.sin(theta * 2 + t * .4)])
        xy, _ = self.projection(xyz, t)
        for i in range(1, len(xy)):
            for j in (max(0, i - 3), max(0, i - 7)):
                a, b = xy[j], xy[i]
                self.path(c, [a,b], "#61E6C4", .22, 1.4)
                fraction = (t * .42 + i * .23) % 1
                p = a + (b - a) * fraction
                c.drawCircle(float(p[0]), float(p[1]), 2.3, paint("#FF6672", .9))
        for i, p in enumerate(xy):
            c.drawCircle(float(p[0]), float(p[1]), 5 + 4 * pulse * (i % 3 == 0), paint("#61E6C4" if i % 3 else "#FF6672", .95))

    def spectrum(self, c, t, bands, level, pulse):
        u = np.linspace(0, 2 * math.pi, 33)
        values = np.r_[bands, bands[0]]
        for layer in range(4):
            r = 165 + 30 * layer + values * (70 + 16 * layer)
            phase = t * .08 + layer * .11
            xyz = np.column_stack([r * np.cos(u + phase), r * np.sin(u + phase), 100 * np.sin(u * 2 + t * .45 + layer * .45)])
            xy, _ = self.projection(xyz, t, scale=1.08)
            self.path(c, xy, "#FF6672" if layer == 1 else "#61E6C4", .95 - layer * .16, 2.5)
            if layer == 0:
                for p in xy[:-1:2]:
                    self.path(c, [(1425, 540), p], "#61E6C4", .13, 1)
        c.drawCircle(1425, 540, 39 + pulse * 12 + level * 9, paint("#61E6C4", .1))
        c.drawCircle(1425, 540, 8 + pulse * 5, paint("#FF6672", .96))
        self.text(c, "AMPLITUDE → FORM", 1425, 905, 18, "#90A4A4", .75, center=True)

    def orbit(self, c, t, level, pulse):
        u = self.angles
        for j in range(5):
            r = 145 + j * 34 + level * 25
            tilt = j * .53 + t * .2
            xyz = np.column_stack([r * np.cos(u), r * np.sin(u) * math.cos(tilt), r * np.sin(u) * math.sin(tilt)])
            xy, _ = self.projection(xyz, t)
            self.path(c, xy, "#FF6672" if j == 2 else "#61E6C4", .84 - j * .10, 2.1)
            for k in (0, 120, 240):
                p = xy[(round(t * (8 + j * 3)) + k) % 360]
                c.drawCircle(float(p[0]), float(p[1]), 4.5 + pulse * 3, paint("#F2F2EA", .97))

    def chrome(self, c, scene, t, light):
        ink = "#080C16" if light else "#F2F2EA"
        muted = "#64736E" if light else "#94A5AA"
        self.text(c, "MOTION / MUSIC STUDY 01", 104, 86, 20, muted, .95)
        self.text(c, f"{self.duration:g} SEC   /   {self.cfg['music']['bpm']:g} BPM", 1510, 86, 20, muted, .95)
        self.text(c, "聲形之間", 104, 984, 23, ink, .85)
        self.text(c, "ORIGINAL MOTION + ORIGINAL MUSIC", 1212, 984, 18, muted, .95)
        start, length = 104, 1712
        for part in self.scenes:
            a = start + part["start"] / self.duration * length
            b = start + part["end"] / self.duration * length
            c.drawLine(a, 1025, b - 5, 1025, paint(ink, .14, 2))
        c.drawLine(start, 1025, start + t / self.duration * length, 1025, paint("#FB626F" if light else "#61E6C4", .92, 3))

    def scene(self, c, scene, t, frame):
        light, u = scene["light"], max(0., t - scene["start"])
        c.drawImage(self.backgrounds[light], 0, 0)
        level = float(min(1., self.levels[frame]))
        role = next(section["role"] for section in self.cfg["sections"] if t < section["end"])
        pulse = self.pulse_at(t)
        self.chrome(c, scene, t, light)
        if scene["kind"] == "outro":
            self.torus(c, t, level, pulse, cx=960, cy=345, scale=.54)
            reveal = ease(u / .85)
            self.text(c, "聲形之間", 960, 665 + (1 - reveal) * 24, 112, "#F2F2EA", reveal, center=True, bold=True)
            self.text(c, "FORM & FREQUENCY", 960, 775, 61, "#61E6C4", ease((u - .30) / .8), center=True)
            self.text(c, "A MOTION & MUSIC STUDY", 960, 855, 21, "#94A5AA", ease((u - .60) / .8), center=True)
            return
        ink = "#080C16" if light else "#F2F2EA"
        accent = "#E85060" if light else "#61E6C4"
        reveal = ease(u / .8)
        self.text(c, scene["kicker"], 104, 250, 21, accent, reveal)
        self.text(c, scene["headline"], 101, 414 + (1 - reveal) * 34,
                  112 if scene["kind"] == "torus" else 94, ink, reveal, width=820, bold=True)
        self.text(c, scene["caption"], 104, 740, 43 if scene["kind"] == "torus" else 37,
                  accent, ease((u - .22) / .8))
        self.text(c, scene["body"], 104, 813, 26, "#596B65" if light else "#9BAFB0",
                  ease((u - .48) / .8), width=820)
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(930, 130, 935, 790))
        if scene["kind"] == "torus":
            self.torus(c, t, level, pulse)
        elif scene["kind"] in ("assembly", "cubes"):
            self.cubes(c, t, u, level, pulse, scene["kind"] == "assembly")
        elif scene["kind"] == "waves":
            self.waves(c, t, level)
        elif scene["kind"] == "network":
            self.network(c, t, u, level, pulse)
        elif scene["kind"] == "spectrum":
            self.spectrum(c, t, self.spectra[frame], level, pulse)
        elif scene["kind"] == "orbit":
            self.orbit(c, t, level, pulse)
        c.restore()

    def frame(self, frame):
        t = frame / self.fps
        index = next(i for i, scene in enumerate(self.scenes) if t < scene["end"])
        c = self.surface.getCanvas()
        scene = self.scenes[index]
        transition = .6
        if index and t - scene["start"] < transition:
            self.scene(c, self.scenes[index - 1], t, frame)
            c.saveLayerAlpha(None, round(255 * ease((t - scene["start"]) / transition)))
            self.scene(c, scene, t, frame)
            c.restore()
        else:
            self.scene(c, scene, t, frame)
        return self.surface.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)

    def preview(self):
        out = self.root / "outputs"
        board = Image.new("RGB", (1920, 1080), "#080C16")
        for i, scene in enumerate(self.scenes):
            t = scene["start"] + min(3., (scene["end"] - scene["start"]) * .5)
            pic = Image.fromarray(self.frame(round(t * self.fps))).convert("RGB")
            pic.save(self.root / "work" / f"preview-{i:02d}.jpg", quality=93)
            board.paste(pic.resize((640, 360), Image.Resampling.LANCZOS), ((i % 3) * 640, (i // 3) * 360))
        board.save(out / "form-and-frequency-storyboard.jpg", quality=94)
        Image.fromarray(self.frame(round(10 * self.fps))).convert("RGB").save(out / "form-and-frequency-poster.jpg", quality=95)
        print("DEMO_PREVIEW_READY", flush=True)

    def render(self):
        work = self.root / "work"
        ff = imageio_ffmpeg.get_ffmpeg_exe()
        command = [ff, "-y", "-hide_banner", "-loglevel", "warning", "-f", "rawvideo", "-pix_fmt", "rgba",
                   "-s", f"{self.w}x{self.h}", "-r", str(self.fps), "-i", "pipe:0", "-an",
                   "-c:v", "libx264", "-threads", "4", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p",
                   "-movflags", "+faststart", str(work / "picture.mp4")]
        with (work / "picture-render.log").open("wb") as log:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=log)
            try:
                for frame in range(round(self.duration * self.fps)):
                    process.stdin.write(self.frame(frame).tobytes())
                    if frame % 300 == 0:
                        print(f"RENDER {frame // self.fps:02d}/{self.duration:g} seconds", flush=True)
                process.stdin.close()
                if process.wait():
                    raise RuntimeError("Video encoder failed; inspect picture-render.log")
            except BaseException:
                process.kill()
                process.wait()
                raise
        print("DEMO_PICTURE_RENDERED", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("preview", "render"))
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    film = Film(args.project)
    getattr(film, args.mode)()
