"""Reusable vector primitives from an original rendered company film."""
import math
import numpy as np
import skia

BLUE, CYAN, GREEN, INK, DARK, MUTED, WHITE = "#0087DC", "#64D7D7", "#B9EB5F", "#062E4A", "#041B2E", "#53748A", "#FFFFFF"
PALETTE = {}

def configure(brand):
    global BLUE, CYAN, GREEN, INK, DARK, MUTED, PALETTE
    BLUE = brand["primary"]
    CYAN = brand["secondary"]
    GREEN = brand["accent"]
    INK = brand["ink"]
    DARK = brand.get("dark", "#071827")
    MUTED = brand.get("muted", "#53748A")
    PALETTE = {"__" + k + "__": globals()[k] for k in ["BLUE", "CYAN", "GREEN", "INK", "DARK", "MUTED"]}

def clamp(x, lo=0., hi=1.):
    return min(hi, max(lo, x))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease(x):
    return 1 - (1 - clamp(x)) ** 3


def lerp(a, b, x):
    return a + (b - a) * x


def rgb(c):
    c = PALETTE.get(c, c)
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def color(c, a=1.):
    r, g, b = rgb(c)
    return skia.ColorSetARGB(round(255 * clamp(a)), r, g, b)


def mix(a, b, t):
    return "#" + "".join(f"{round(lerp(x, y, t)):02X}" for x, y in zip(rgb(a), rgb(b)))


def paint(c, a=1., stroke=0, blur=0):
    p = skia.Paint(AntiAlias=True, Color=color(c, a))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.BlurStyle.kNormal_BlurStyle, blur))
    return p


def line(c, pts, fill="__BLUE__", width=2, a=1):
    if len(pts) < 2:
        return
    p = skia.Path()
    p.moveTo(*pts[0])
    for xy in pts[1:]:
        p.lineTo(*xy)
    c.drawPath(p, paint(fill, a, width))


def poly(c, pts, fill, a=1, stroke=None, width=2):
    p = skia.Path()
    p.moveTo(*pts[0])
    for xy in pts[1:]:
        p.lineTo(*xy)
    p.close()
    if fill:
        c.drawPath(p, paint(fill, a))
    if stroke:
        c.drawPath(p, paint(stroke, a, width))


def rect(c, x, y, w, h, fill, a=1, radius=0, stroke=0):
    p = paint(fill, a, stroke)
    r = skia.Rect.MakeXYWH(x, y, w, h)
    if radius:
        c.drawRoundRect(r, radius, radius, p)
    else:
        c.drawRect(r, p)


def circle(c, x, y, r, fill, a=1, stroke=0):
    c.drawCircle(x, y, max(.01, r), paint(fill, a, stroke))


def glow(c, x, y, r, fill, a=.12):
    p = paint(fill)
    p.setShader(skia.GradientShader.MakeRadial((x, y), r,
        [color(fill, a), color(fill, 0)], [0., 1.]))
    c.drawCircle(x, y, r, p)


def cubic(c, p0, p1, p2, p3, fill, width=3, a=1):
    path = skia.Path()
    path.moveTo(*p0)
    path.cubicTo(*p1, *p2, *p3)
    c.drawPath(path, paint(fill, a, width))


def path_flow(c, pts, t, fill="__CYAN__", width=4, count=4, a=1, speed=.18):
    line(c, pts, fill, width, a * .2)
    seg = np.array(pts, dtype=float)
    dist = np.linalg.norm(np.diff(seg, axis=0), axis=1)
    total = dist.sum()
    cum = np.concatenate([[0.], np.cumsum(dist)])
    for k in range(count):
        target = ((t * speed + k / count) % 1) * total
        idx = min(len(dist) - 1, int(np.searchsorted(cum, target, side="right") - 1))
        f = (target - cum[idx]) / max(.01, dist[idx])
        q = seg[idx] * (1 - f) + seg[idx + 1] * f
        circle(c, *q, width * 1.55, fill, a)
        circle(c, *q, width * 3.5, fill, a * .14)


def loop3d(c, x, y, radius, t, dark=False, build=1, thickness=30):
    """A dimensional, energy-loop inspired ribbon, not a modified logo."""
    n = 150
    points = []
    rot = .45 + .12 * math.sin(t * .24)
    tilt = .62
    for j in range(n + 1):
        th = 2 * math.pi * j / n + t * .18
        X = radius * math.cos(th)
        Y = radius * math.sin(th)
        Z = radius * .23 * math.sin(th * 2 + t * .25)
        X, Z = X * math.cos(rot) + Z * math.sin(rot), -X * math.sin(rot) + Z * math.cos(rot)
        Y, Z = Y * math.cos(tilt) - Z * math.sin(tilt), Y * math.sin(tilt) + Z * math.cos(tilt)
        perspective = 1 + Z / 1700
        points.append((x + X * perspective, y + Y * perspective, Z, th))
    segments = []
    for j in range(n):
        if j / n > build:
            continue
        p, q = points[j], points[j + 1]
        z = (p[2] + q[2]) / 2
        cc = BLUE if j < n * .64 else CYAN if j < n * .85 else GREEN
        cc = mix(cc, WHITE if not dark else mix(BLUE, INK, .25), .08 + .22 * clamp(-z / radius))
        segments.append((z, p, q, cc))
    for z, p, q, cc in sorted(segments, key=lambda s: s[0]):
        width = thickness * (1 + z / 1500)
        line(c, [(p[0] + 7, p[1] + 11), (q[0] + 7, q[1] + 11)], INK, width + 10, .055 if not dark else .11)
        line(c, [p[:2], q[:2]], cc, width)
        line(c, [(p[0], p[1] - width * .27), (q[0], q[1] - width * .27)], WHITE, 2, .20)
    for j in range(18):
        th = t * .4 + j * math.tau / 18
        rr = radius + 35 + 14 * math.sin(j)
        px, py = x + rr * math.cos(th), y + rr * .68 * math.sin(th)
        circle(c, px, py, 2.5 + 1.7 * (math.sin(th) + 1), CYAN if dark else BLUE, .4)


def chip_icon(c, x, y, size, t=0, dark=False):
    cc = CYAN if dark else BLUE
    rect(c, x - size / 2, y - size / 2, size, size, cc, .1, 12)
    rect(c, x - size * .33, y - size * .33, size * .66, size * .66, cc, .8, 8, 3)
    for j in range(5):
        off = (j - 2) * size * .13
        for sign in (-1, 1):
            line(c, [(x + sign * size * .35, y + off), (x + sign * size * .57, y + off)], cc, 3, .7)
            line(c, [(x + off, y + sign * size * .35), (x + off, y + sign * size * .57)], cc, 3, .7)
    rect(c, x - size * .17, y - size * .17, size * .34, size * .34, cc, .35 + .2 * math.sin(t * 4), 5)


def iso(origin, x, y, z=0, scale=1.):
    return origin[0] + (x - y) * .866 * scale, origin[1] + (x + y) * .5 * scale - z * scale


def box(c, origin, x, y, z, dx, dy, dz, dark=True, accent="__BLUE__", a=1, wire=False):
    # Faces in correct orthographic draw order; fixed geometry in a coherent world.
    p = lambda X, Y, Z: iso(origin, X, Y, Z)
    top = [p(x, y, z + dz), p(x + dx, y, z + dz), p(x + dx, y + dy, z + dz), p(x, y + dy, z + dz)]
    front = [p(x, y + dy, z), p(x + dx, y + dy, z), p(x + dx, y + dy, z + dz), p(x, y + dy, z + dz)]
    side = [p(x + dx, y, z), p(x + dx, y + dy, z), p(x + dx, y + dy, z + dz), p(x + dx, y, z + dz)]
    if dark:
        fills = [mix(accent, DARK, .62), mix(accent, DARK, .70), mix(accent, DARK, .82)]
        edge = CYAN
    else:
        fills = [mix(accent, WHITE, .87), mix(accent, WHITE, .68), mix(accent, WHITE, .50)]
        edge = mix(accent, INK, .25)
    for face, fill in zip([front, side, top], [fills[1], fills[2], fills[0]]):
        poly(c, face, None if wire else fill, a, edge, 1.6 if wire else 1.3)
    return top, front, side


def grid3d(c, origin, t, dark=True, extent=340):
    gc = CYAN if dark else BLUE
    for k in range(-extent, extent + 1, 60):
        line(c, [iso(origin, k, -extent), iso(origin, k, extent)], gc, 1, .13)
        line(c, [iso(origin, -extent, k), iso(origin, extent, k)], gc, 1, .13)
    pts = [iso(origin, -extent, -extent), iso(origin, extent, -extent), iso(origin, extent, extent), iso(origin, -extent, extent), iso(origin, -extent, -extent)]
    path_flow(c, pts, t, gc, 2, 6, .45, .04)


def rack(c, origin, x, y, u, t, idx=0, dark=True, height=210):
    p = ease((u - .13 * idx) / 1.2)
    z = (1 - p) * 240
    box(c, origin, x, y, z, 86, 96, height, dark, BLUE, p)
    for j in range(8):
        zslot = z + 20 + j * (height - 40) / 8
        left = iso(origin, x + 9, y + 96.5, zslot)
        right = iso(origin, x + 77, y + 96.5, zslot)
        line(c, [left, right], CYAN if dark else BLUE, 4, .45 * p)
        led = iso(origin, x + 67, y + 97.5, zslot + 8)
        circle(c, *led, 2.6, GREEN, p * (.3 + .7 * (math.sin(t * 6 + j + idx) > 0)))


def globe(c, cx, cy, r, t, build=1):
    ang = t * .13
    def pr(lon, lat):
        X = math.cos(lat) * math.sin(lon + ang)
        Y = math.sin(lat)
        Z = math.cos(lat) * math.cos(lon + ang)
        return cx + r * X, cy - r * Y, Z
    circle(c, cx, cy, r, BLUE, .045)
    circle(c, cx, cy, r, BLUE, .2, 1)
    for lat in np.linspace(-1.2, 1.2, 9):
        pts = [pr(lon, lat)[:2] for lon in np.linspace(-math.pi - ang, math.pi - ang, 90)]
        line(c, pts, BLUE, 1, .10 * build)
    for lon in np.linspace(0, math.tau, 14, endpoint=False):
        pts = [pr(lon, lat)[:2] for lat in np.linspace(-math.pi / 2, math.pi / 2, 60)]
        line(c, pts, BLUE, 1.2, .18 * build)
    rng = np.random.default_rng(42)
    positions = [(rng.uniform(-math.pi, math.pi), rng.uniform(-1.15, 1.15)) for _ in range(42)]
    visible = []
    for j, (lon, lat) in enumerate(positions):
        X, Y, Z = pr(lon, lat)
        if Z > -.1 and build > j / 100:
            p = clamp((build - j / 100) * 10)
            circle(c, X, Y, 3.5 + 1.2 * math.sin(t * 2 + j), BLUE, p * (.5 + .5 * Z))
            if j % 7 == 0:
                circle(c, X, Y, 9 + 7 * ((t * .5 + j) % 1), CYAN, .4 * p, 1.5)
            visible.append((X, Y, Z))
    for j in range(0, len(visible) - 3, 4):
        x1, y1, _ = visible[j]
        x2, y2, _ = visible[j + 3]
        cubic(c, (x1, y1), (x1, y1 - 100), (x2, y2 - 100), (x2, y2), BLUE, 1.5, .20 * build)
