"""Configurable 16:9 vector motion starter with brand-safe logo geometry."""
import argparse
from functools import lru_cache
import math
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

import imageio_ffmpeg
import numpy as np
from PIL import Image
import skia

import drawing as d
from projectlib import load, local_path, scene_at


class Renderer:
    def __init__(self, root, cfg):
        self.root, self.cfg = root, cfg
        self.width, self.height = cfg["width"], cfg["height"]
        if abs(self.width / self.height - 16 / 9) > .005:
            raise ValueError("This starter composition is 16:9. Redesign its layout for another aspect ratio.")
        d.configure(cfg["brand"])
        self.logo_light = self.load_logo(cfg["brand"].get("logo"))
        self.logo_dark = self.load_logo(cfg["brand"].get("logo_on_dark"))
        self.bg = {theme: self.background(theme) for theme in ("light", "dark")}
        self.surface = skia.Surface.MakeRaster(skia.ImageInfo.Make(self.width, self.height,
                            skia.ColorType.kRGBA_8888_ColorType, skia.AlphaType.kPremul_AlphaType))

    @lru_cache(maxsize=128)
    def font(self, size, cn=True, bold=True):
        config = self.cfg.get("fonts", {})
        path = local_path(self.root, config.get("cn" if cn else "en"))
        if path is None:
            candidates = (["C:/Windows/Fonts/msjhbd.ttc" if bold else "C:/Windows/Fonts/msjh.ttc",
                           "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"] if cn else
                          ["C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
                           "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
            path = next((Path(x) for x in candidates if Path(x).exists()), None)
        face = skia.Typeface.MakeFromFile(str(path)) if path else None
        if face is None:
            raise FileNotFoundError("Set fonts.cn / fonts.en to local font files with the required glyphs")
        font = skia.Font(face, size)
        font.setEdging(skia.Font.Edging.kAntiAlias)
        return font

    def text(self, canvas, text, x, y, size, fill, alpha=1., center=False, cn=True, bold=True, max_width=None):
        for row, line in enumerate(str(text).splitlines()):
            line_cn = cn or any("\u3400" <= char <= "\u9fff" for char in line)
            actual = size
            font = self.font(actual, line_cn, bold)
            width = font.measureText(line)
            if max_width and width > max_width:
                actual = size * max_width / width
                font = self.font(actual, line_cn, bold)
                width = font.measureText(line)
            canvas.drawString(line, x - width / 2 if center else x, y + row * size * 1.25, font, d.paint(fill, alpha))

    def reveal(self, canvas, text, x, y, size, u, delay, color, **kwargs):
        p = d.ease((u - delay) / .72)
        self.text(canvas, text, x, y + (1 - p) * 30, size, color, p, **kwargs)

    def load_logo(self, value):
        path = local_path(self.root, value)
        if not path:
            return None
        if path.suffix.lower() != ".svg":
            arr = np.array(Image.open(path).convert("RGBA"))
            return skia.Image.fromarray(arr), arr.shape[1] / arr.shape[0]
        data = path.read_bytes()
        xml = ET.fromstring(data)
        view = xml.attrib.get("viewBox")
        if view:
            _, _, width, height = [float(x) for x in re.split(r"[\s,]+", view.strip())]
        else:
            width = float(re.sub(r"[^0-9.]", "", xml.attrib.get("width", "1000")))
            height = float(re.sub(r"[^0-9.]", "", xml.attrib.get("height", "300")))
        if width <= 0 or height <= 0:
            raise ValueError("Invalid SVG dimensions")
        ratio = width / height
        dom = skia.SVGDOM.MakeFromStream(skia.MemoryStream(data))
        if dom is None:
            raise ValueError("SVG parsing failed; use a faithful PNG conversion")
        w, h = 1400, max(1, round(1400 / ratio))
        dom.setContainerSize(skia.Size(w, h))
        surface = skia.Surface(w, h)
        surface.getCanvas().clear(skia.ColorTRANSPARENT)
        dom.render(surface.getCanvas())
        return surface.makeImageSnapshot(), ratio

    def logo(self, canvas, x, y, width, dark=False, alpha=1., max_height=200):
        logo = self.logo_dark if dark and self.logo_dark else self.logo_light
        if logo:
            img, ratio = logo
            width = min(width, max_height * ratio)
            canvas.drawImageRect(img, skia.Rect.MakeXYWH(x, y, width, width / ratio),
                                skia.SamplingOptions(skia.FilterMode.kLinear), skia.Paint(Alphaf=alpha))
        else:
            self.text(canvas, self.cfg["brand"]["name"], x, y + 56, 54, d.WHITE if dark else d.BLUE, alpha, max_width=width)

    def background(self, theme):
        surface = skia.Surface(1920, 1080)
        canvas = surface.getCanvas()
        first, second = ((d.DARK, d.mix(d.BLUE, d.DARK, .82)) if theme == "dark" else
                         (d.WHITE, d.mix(d.BLUE, d.WHITE, .94)))
        paint = skia.Paint()
        paint.setShader(skia.GradientShader.MakeLinear([(0, 0), (1920, 1080)], [d.color(first), d.color(second)]))
        canvas.drawRect(skia.Rect.MakeWH(1920, 1080), paint)
        for x in range(60, 1920, 80):
            for y in range(40, 1080, 80):
                d.circle(canvas, x, y, 1.2, d.CYAN if theme == "dark" else d.BLUE, .08)
        return surface.makeImageSnapshot()

    def graphic(self, canvas, kind, u, t, dark, scene):
        color = d.CYAN if dark else d.BLUE
        if kind in ("intro", "outro"):
            if kind == "intro":
                d.loop3d(canvas, 1400, 550, 340, t, dark, d.ease(u / 1.4), 42)
                d.chip_icon(canvas, 1400, 550, 145, t, dark)
            else:
                d.loop3d(canvas, -45, 880, 300, t, dark, 1., 30)
                d.loop3d(canvas, 1970, 790, 300, t + 2, dark, 1., 30)
        elif kind == "network":
            canvas.save()
            canvas.translate(1420, 560)
            for j in range(18):
                a = j * math.tau / 18 + t * .055
                r = 220 + 70 * math.sin(j * 1.9)
                x, y = math.cos(a) * r, math.sin(a) * r * .8
                d.line(canvas, [(0, 0), (x, y)], color, 1.4, .25)
                d.circle(canvas, x, y, 8 + 2 * math.sin(t * 2 + j), color, .7)
                d.path_flow(canvas, [(0, 0), (x, y)], t + j, d.GREEN, 2, 2, .7, .18)
            d.loop3d(canvas, 0, 0, 350, t, dark, d.ease(u / 1.5), 12)
            d.chip_icon(canvas, 0, 0, 112, t, dark)
            canvas.restore()
        elif kind == "modules":
            origin = (1420, 710)
            d.grid3d(canvas, origin, t, dark)
            for j, (x, y) in enumerate([(-180, -60), (-60, -60), (60, -60), (-180, 90), (-60, 90), (60, 90)]):
                d.rack(canvas, origin, x, y, u, t, j, dark, 200 + (j % 3) * 32)
            points = [d.iso(origin, -230, 240), d.iso(origin, 250, 240), d.iso(origin, 250, -240)]
            d.path_flow(canvas, points, t, d.GREEN, 4, 6, d.ease(u / 1.5), .13)
        elif kind == "flow":
            pts = [(1060, 400), (1230, 400), (1230, 730), (1540, 730), (1540, 490), (1740, 490)]
            d.path_flow(canvas, pts, t, color, 5, 11, d.ease(u / 1.5), .12)
            for j, (x, y) in enumerate([(1080, 400), (1390, 730), (1740, 490)]):
                d.circle(canvas, x, y, 94, d.DARK if dark else d.WHITE)
                d.circle(canvas, x, y, 95, color, .4, 2)
                d.chip_icon(canvas, x, y, 110, t + j, dark)
            d.loop3d(canvas, 1410, 550, 350, t, dark, .8, 8)
        elif kind == "metric":
            value = scene.get("metric_value")
            d.circle(canvas, 1430, 555, 270, color, .15, 25)
            if value is not None:
                value = max(0., min(100., float(value)))
                p = d.ease(u / 1.6)
                arc = skia.Path()
                arc.addArc(skia.Rect.MakeLTRB(1160, 285, 1700, 825), -90, value * 3.6 * p)
                canvas.drawPath(arc, d.paint(d.GREEN, 1., 25))
                self.text(canvas, f"{value:g}%", 1430, 620, 155, d.WHITE if dark else d.BLUE, center=True, cn=False)
            else:
                d.loop3d(canvas, 1430, 555, 280, t, dark, 1., 24)
                d.chip_icon(canvas, 1430, 555, 130, t, dark)
        else:
            raise ValueError(f"Unknown scene kind: {kind}")

    def render(self, time):
        canvas = self.surface.getCanvas()
        canvas.save()
        canvas.scale(self.width / 1920, self.height / 1080)
        index, scene = scene_at(self.cfg, time)
        u = time - scene["start"]
        dark = scene.get("scheme", "light") == "dark"
        fg = d.WHITE if dark else d.INK
        canvas.drawImage(self.bg["dark" if dark else "light"], 0, 0)
        kind = scene["kind"]
        self.graphic(canvas, kind, u, time, dark, scene)
        if kind == "outro":
            logo = self.logo_dark if dark and self.logo_dark else self.logo_light
            effective = min(720, 220 * logo[1]) if logo else 600
            self.logo(canvas, 960 - effective / 2, 180, 720, dark, d.ease(u / .8), 220)
            self.reveal(canvas, scene["headline"], 960, 595, 82, u, .4, fg, center=True, max_width=1300)
            self.reveal(canvas, scene["body"], 960, 737, 43, u, .8, fg, center=True, bold=False, max_width=1250)
            d.rect(canvas, 710, 868, 500 * d.ease(u / 1.3), 5, d.BLUE)
        else:
            if kind == "intro":
                self.logo(canvas, 110, 175, 450, dark, d.ease(u / .8), 150)
            y = 467 if kind == "intro" else 284
            self.reveal(canvas, scene["headline"], 110, y, 83, u, .12, fg, max_width=845)
            lines = len(scene["headline"].splitlines())
            body_y = y + max(1, lines) * 105 + 60
            self.reveal(canvas, scene["body"], 118, body_y, 37, u, .6, fg, bold=False, max_width=830)
            if scene.get("metric"):
                self.reveal(canvas, str(scene["metric"]) + str(scene.get("suffix", "")), 110, 775, 142, u, .85,
                            d.CYAN if dark else d.BLUE, cn=False, max_width=800)
                self.reveal(canvas, scene.get("label", ""), 120, 860, 32, u, 1.1, fg, bold=False, max_width=830)
            self.text(canvas, scene.get("visual_label", ""), 1430, 910, 25, d.CYAN if dark else d.BLUE,
                      .7, center=True, cn=False, max_width=700)
        self.text(canvas, f"{index + 1:02d}  |  " + scene["chapter"], 108, 100, 25, fg, .65, cn=False, max_width=1280)
        if kind != "outro":
            self.logo(canvas, 1625, 50, 190, dark, max_height=65)
        self.text(canvas, scene.get("footnote", ""), 108, 1008, 24, fg, .63, bold=False, max_width=1700)
        d.rect(canvas, 0, 1075, 1920 * d.clamp(time / self.cfg["duration"]), 5, d.BLUE)
        # Wipe duration adapts to short scenes and preserves the explicit cut time.
        for boundary_index in range(1, len(self.cfg["scenes"])):
            left = self.cfg["scenes"][boundary_index - 1]
            right = self.cfg["scenes"][boundary_index]
            half = min(.32, (left["end"] - left["start"]) / 6, (right["end"] - right["start"]) / 6)
            dt = time - right["start"]
            if abs(dt) < half:
                x = d.lerp(2600, -2100, d.smooth((dt + half) / (half * 2)))
                for off, width, color in [(0, 1080, d.BLUE), (1080, 180, d.CYAN), (1260, 160, d.GREEN)]:
                    d.poly(canvas, [(x + off, -100), (x + off + width, -100),
                                   (x + off + width - 760, 1180), (x + off - 760, 1180)], color)
                break
        canvas.restore()
        return self.surface.makeImageSnapshot()

    def save(self, time, dest):
        arr = self.render(time).toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)
        Image.fromarray(arr).convert("RGB").save(dest)

    def preview(self):
        folder = self.root / "work" / "frames"
        folder.mkdir(exist_ok=True)
        tiles = []
        for i, scene in enumerate(self.cfg["scenes"]):
            dest = folder / f"{i:02d}.png"
            self.save(scene["start"] + (scene["end"] - scene["start"]) * .58, dest)
            tiles.append(Image.open(dest).resize((640, 360)))
        rows = math.ceil(len(tiles) / 2)
        sheet = Image.new("RGB", (1280, rows * 360), "white")
        for i, tile in enumerate(tiles):
            sheet.paste(tile, (i % 2 * 640, i // 2 * 360))
        sheet.save(self.root / "outputs" / f"{self.cfg['slug']}-storyboard.jpg", quality=93)
        self.save(self.cfg["scenes"][0]["end"] * .58, self.root / "outputs" / f"{self.cfg['slug']}-poster.jpg")
        print("PREVIEW_COMPLETE", flush=True)

    def film(self):
        frames = round(self.cfg["duration"] * self.cfg["fps"])
        command = [imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
                   "-pix_fmt", "rgba", "-s", f"{self.width}x{self.height}", "-r", str(self.cfg["fps"]), "-i", "pipe:0",
                   "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
                   "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-movflags", "+faststart",
                   str(self.root / "work" / "picture.mp4")]
        with (self.root / "work" / "picture-render.log").open("wb") as log:
            proc = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=log)
            try:
                for frame in range(frames):
                    proc.stdin.write(self.render(frame / self.cfg["fps"]).tobytes())
                    if frame % max(1, round(self.cfg["fps"] * 5)) == 0:
                        print(f"PICTURE {frame}/{frames}", flush=True)
                proc.stdin.close()
                if proc.wait():
                    raise RuntimeError("Encoding failed; see work/picture-render.log")
            except BaseException:
                proc.kill()
                proc.wait()
                raise
        print("PICTURE_COMPLETE", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=["preview", "render"])
    ap.add_argument("--project", type=Path, required=True)
    args = ap.parse_args()
    root, cfg = load(args.project)
    renderer = Renderer(root, cfg)
    renderer.preview() if args.mode == "preview" else renderer.film()
