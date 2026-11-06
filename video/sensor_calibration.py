#!/usr/bin/env python3
"""Measure the A7M5's S-Gamut3(.Cine) -> white-balanced camera RGB relation.

Photo and S-Log3 video of the same screen chart see the same sensor, so their
patch values differ only by the camera's video matrix (plus exposure).  The
fitted matrix lets video_look.py send video straight into the photo look chain
(camera RGB -> F_L) without the ST reference convention.

    sensor_calibration.py chart [--out chart.html]
    sensor_calibration.py fit PHOTO.ARW CLIP.MP4 [--gamut SGamut3Cine] [--out calib.json]

Capture: tripod, no ND / VND, dark room, screen brightness and True Tone /
Night Shift fixed; identical manual WB (Kelvin), ISO, aperture and shutter for
the RAW and the S-Log3 clip; slightly defocused against moire.
"""
from __future__ import annotations

import argparse
import colorsys
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for p in (HERE, ROOT / "sonylook"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import video_color as V  # noqa: E402

# Chart geometry, in chart units (16:9 canvas).
CANVAS = (1600.0, 900.0)
MARKER_SIZE = 70.0
MARKERS = np.array([[50, 50], [1550, 50], [50, 850], [1550, 850]], float)  # TL TR BL BR centres
GRID_ORIGIN = (120.0, 30.0)
COLS, ROWS = 16, 9
PITCH = ((1480.0 - 120.0) / COLS, (870.0 - 30.0) / ROWS)
PATCH_FILL = 0.8          # patch side / pitch
SAMPLE_FILL = 0.45        # sampled side / pitch
SURROUND = 0.08           # encoded display-p3 grey between patches
# (saturation, value) per colour row, in encoded display-p3 HSV.
COLOUR_ROWS = [(1.0, .8), (.7, .8), (.45, .8), (.22, .8), (1.0, .5), (.6, .5), (1.0, .3), (.5, .3)]


def patches():
    """[(col, row, display-p3 encoded rgb)], row 0 a grey ramp, then 16 hues per row."""
    out = [(c, 0, (g, g, g)) for c, g in enumerate(np.linspace(.03, .8, COLS))]
    for r, (s, v) in enumerate(COLOUR_ROWS, start=1):
        for c in range(COLS):
            out.append((c, r, colorsys.hsv_to_rgb(c / COLS, s, v)))
    return out


def patch_centre(col, row):
    return (GRID_ORIGIN[0] + (col + .5) * PITCH[0], GRID_ORIGIN[1] + (row + .5) * PITCH[1])


def chart_html():
    w, h = CANVAS
    p3 = lambda rgb: "color(display-p3 {:.4f} {:.4f} {:.4f})".format(*rgb)  # noqa: E731
    items = []
    for col, row, rgb in patches():
        cx, cy = patch_centre(col, row)
        pw, ph = PITCH[0] * PATCH_FILL, PITCH[1] * PATCH_FILL
        items.append(f'<rect x="{cx - pw / 2:.2f}" y="{cy - ph / 2:.2f}" width="{pw:.2f}" '
                     f'height="{ph:.2f}" style="fill:{p3(rgb)}"/>')
    for x, y in MARKERS:
        m = MARKER_SIZE
        items.append(f'<rect x="{x - m / 2}" y="{y - m / 2}" width="{m}" height="{m}" fill="#fff"/>')
    surround = p3((SURROUND,) * 3)
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sensor Calibration Chart</title>
<style>
  html, body {{ margin: 0; height: 100%; background: #000; overflow: hidden; cursor: none; }}
  svg {{ width: 100vw; height: 100vh; display: block; }}
  #hint {{ position: fixed; inset: auto 0 0 0; padding: 10px 16px; font: 14px -apple-system, sans-serif;
          color: #aaa; background: #000; text-align: center; cursor: default; }}
</style></head>
<body>
<svg viewBox="0 0 {w:g} {h:g}" preserveAspectRatio="xMidYMid meet">
  <rect width="{w:g}" height="{h:g}" style="fill:{surround}"/>
  {''.join(items)}
</svg>
<div id="hint">点击进入全屏，拍摄期间不要移动窗口或调整亮度。（Click for full screen.）</div>
<script>
  document.body.addEventListener('click', () => {{
    document.documentElement.requestFullscreen?.();
    document.getElementById('hint').remove();
  }}, {{ once: true }});
</script>
</body></html>
"""


# ---------------------------------------------------------------- detection
def homography(src, dst):
    """3x3 H with dst ~ H @ [src, 1] from four or more point pairs (DLT)."""
    rows = []
    for (x, y), (u, v) in zip(src, dst):
        rows.append([x, y, 1, 0, 0, 0, -u * x, -u * y, -u])
        rows.append([0, 0, 0, x, y, 1, -v * x, -v * y, -v])
    h = np.linalg.svd(np.asarray(rows, float))[2][-1]
    return (h / h[-1]).reshape(3, 3)


def apply_h(h, pts):
    pts = np.asarray(pts, float)
    p = np.c_[pts, np.ones(len(pts))] @ h.T
    return p[:, :2] / p[:, 2:]


def find_markers(rgb):
    """Centres (x, y) of the four white corner squares, ordered TL TR BL BR."""
    from scipy import ndimage
    lum = np.asarray(rgb, float).mean(axis=-1)
    # Segment the light patches and markers alike (lamps or UI elsewhere in frame can be
    # brighter than the markers), keep square blobs of patch size, then take the brightest four.
    labels, n = ndimage.label(lum > 0.3 * np.percentile(lum, 99.5))
    index = np.arange(1, n + 1)
    areas = ndimage.sum_labels(np.ones_like(lum), labels, index)
    means = ndimage.mean(lum, labels, index)
    fill = np.array([areas[i] / ((s[0].stop - s[0].start) * (s[1].stop - s[1].start))
                     for i, s in enumerate(ndimage.find_objects(labels))])
    square = (fill > 0.85) & (areas > 50)
    if square.sum() < 4:
        raise ValueError(f"found {square.sum()} square blobs; expected the four white markers")
    typical = np.median(areas[square])
    candidates = np.flatnonzero(square & (areas > 0.4 * typical) & (areas < 2.5 * typical))
    if len(candidates) < 4:
        raise ValueError("could not find four patch-sized markers; check exposure and framing")
    # Vignetting dims the corners, so brightness alone is not decisive: of the brightest
    # blobs, the markers are the ones furthest out towards each corner.
    pool = candidates[np.argsort(means[candidates])[-12:]]
    centres = np.array(ndimage.center_of_mass(np.ones_like(lum), labels, pool + 1))[:, ::-1]
    s, d = centres.sum(1), centres[:, 0] - centres[:, 1]
    order = [np.argmin(s), np.argmax(d), np.argmin(d), np.argmax(s)]   # TL TR BL BR
    if len(set(order)) != 4:
        raise ValueError("could not order the four markers")
    return centres[order]


def sample_patches(rgb, markers, n=7):
    """Median RGB per patch over a central n x n grid of sample points."""
    rgb = np.asarray(rgb, float)
    h = homography(MARKERS, markers)
    offsets = (np.linspace(-.5, .5, n) * SAMPLE_FILL)
    out = []
    for col, row, _ in patches():
        cx, cy = patch_centre(col, row)
        pts = np.array([(cx + ox * PITCH[0], cy + oy * PITCH[1]) for oy in offsets for ox in offsets])
        xy = np.rint(apply_h(h, pts)).astype(int)
        if (xy < 0).any() or (xy[:, 0] >= rgb.shape[1]).any() or (xy[:, 1] >= rgb.shape[0]).any():
            raise ValueError("patch outside the image; the whole chart must be in frame")
        out.append(np.median(rgb[xy[:, 1], xy[:, 0]], axis=0))
    return np.array(out)


# ---------------------------------------------------------------- fit
def fit_matrix(video, photo, weights=None):
    """Least-squares M with photo ~ video @ M.T, factored as M = s * diag(wb) @ N.

    N keeps equal RGB equal (N @ 1 = 1): the colour relation between the modes.
    wb (mean 1) is the white-balance difference between the two shots, which need
    not match exactly; s is the exposure relation.  Returns (N, s, wb)."""
    x, y = np.asarray(video, float), np.asarray(photo, float)
    w = np.ones(len(x)) if weights is None else np.asarray(weights, float)
    m = np.linalg.lstsq(x * w[:, None], y * w[:, None], rcond=None)[0].T
    sums = m @ np.ones(3)
    s = float(sums.mean())
    return m / sums[:, None], s, sums / s


# ---------------------------------------------------------------- I/O
def read_video(path, seconds=1.0, width=1920):
    """Average of the first `seconds` of the clip as full-code S-Log3 (CV / 1023)."""
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                            "stream=width,height", "-of", "csv=p=0", str(path)],
                           capture_output=True, text=True, check=True).stdout.split(",")
    w0, h0 = int(probe[0]), int(probe[1])
    height = round(width * h0 / w0 / 2) * 2
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-t", str(seconds), "-vf",
                          f"scale={width}:{height}:in_color_matrix=bt709:in_range=full:"
                          "out_range=full:flags=area,format=rgb48le", "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    frames = np.frombuffer(raw, np.uint16).reshape(-1, height, width, 3)
    return frames.mean(axis=0) / 65535.0, len(frames)


def read_photo(arw, scale=4):
    import sony_render as R
    return R.front_end_sony(str(arw), scale=scale) / 16384.0


def sha256(path, limit=64 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read(limit))
    return h.hexdigest()


def overlay(rgb, markers, path):
    from PIL import Image, ImageDraw
    img = np.clip(np.asarray(rgb, float) / max(np.percentile(rgb, 99.5), 1e-9), 0, 1) ** (1 / 2.2)
    im = Image.fromarray((img * 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    h = homography(MARKERS, markers)
    for col, row, _ in patches():
        cx, cy = patch_centre(col, row)
        hw, hh = SAMPLE_FILL * PITCH[0] / 2, SAMPLE_FILL * PITCH[1] / 2
        q = apply_h(h, [(cx - hw, cy - hh), (cx + hw, cy - hh), (cx + hw, cy + hh), (cx - hw, cy + hh)])
        d.polygon([tuple(p) for p in q], outline=(255, 0, 255))
    for x, y in markers:
        d.ellipse((x - 6, y - 6, x + 6, y + 6), outline=(0, 255, 0), width=2)
    im.save(path)


def fit_command(a):
    photo = read_photo(a.arw, a.photo_scale)
    code, frames = read_video(a.clip, a.seconds)
    photo_p = sample_patches(photo, find_markers(photo))
    video_markers = find_markers(V.slog3_decode(code))   # log codes compress the markers
    video_code = sample_patches(code, video_markers)
    video_p = V.slog3_decode(video_code)
    clipped_photo = photo_p.max(1) > 16000 / 16384
    clipped_video = video_code.max(1) > 0.94
    dark = photo_p.mean(1) < 0.004
    use = ~(clipped_photo | clipped_video | dark)
    if use.sum() < 30:
        raise SystemExit(f"only {use.sum()} usable patches (clipped photo {clipped_photo.sum()}, "
                         f"clipped video {clipped_video.sum()}, too dark {dark.sum()}); fix exposure")
    weights = 1 / np.maximum(photo_p[use].sum(1), 1e-6)       # equalise relative error
    m, s, wb = fit_matrix(video_p[use], photo_p[use], weights)
    pred = video_p @ m.T * (s * wb)
    rel = np.abs(pred - photo_p) / np.maximum(photo_p.max(1, keepdims=True), 1e-6)
    grey = np.array([r == 0 for _, r, _ in patches()]) & use
    report = {
        "version": 2,
        "gamut": a.gamut,
        "matrix": m.tolist(),
        "matrix_meaning": f"{a.gamut} linear (S-Log3 decoded) -> white-balanced A7M5 camera RGB, "
                          "normalised so equal RGB maps to equal RGB",
        "exposure_scale": s,
        "exposure_scale_meaning": "photo camera RGB (Sony native / 16384) per unit S-Log3 scene "
                                  "reflection, valid when both shots used the same ISO/aperture/shutter",
        "white_balance_difference": wb.tolist(),
        "white_balance_difference_meaning": "photo / video per-channel gain on neutrals (mean 1); "
                                            "removed from the matrix",
        "patches_used": int(use.sum()), "patches_total": len(use),
        "excluded": {"photo_clipped": int(clipped_photo.sum()), "video_clipped": int(clipped_video.sum()),
                     "too_dark": int(dark.sum())},
        "relative_error_used": {"mean": float(rel[use].mean()), "p95": float(np.percentile(rel[use], 95)),
                                "max": float(rel[use].max())},
        "grey_ramp_ratio_photo_over_video": (photo_p[grey].mean(1) / video_p[grey].mean(1)).tolist(),
        "video_frames_averaged": frames,
        "sources": {"arw": str(a.arw), "arw_sha256_first64MB": sha256(a.arw),
                    "clip": str(a.clip), "clip_sha256_first64MB": sha256(a.clip)},
        "patches": [{"col": c, "row": r, "display_p3": list(map(float, rgb)), "used": bool(u),
                     "photo": p.tolist(), "video_linear": v.tolist()}
                    for (c, r, rgb), u, p, v in zip(patches(), use, photo_p, video_p)],
    }
    a.out.write_text(json.dumps(report, indent=2) + "\n")
    stem = a.out.with_suffix("")
    overlay(photo, find_markers(photo), f"{stem}_photo_samples.png")
    overlay(code, video_markers, f"{stem}_video_samples.png")
    np.set_printoptions(precision=4, suppress=True)
    print(f"{use.sum()}/{len(use)} patches; matrix ({a.gamut} -> camera RGB):\n{m}")
    print(f"white-balance difference (photo/video) {wb.round(4)}")
    print(f"exposure scale {s:.5f}; relative error mean {rel[use].mean():.4f}, "
          f"p95 {np.percentile(rel[use], 95):.4f}")
    print(f"wrote {a.out} and sample overlays {stem}_*_samples.png")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("chart", help="write the full-screen display-p3 chart page")
    c.add_argument("--out", type=Path, default=HERE / "calibration_chart.html")
    f = sub.add_parser("fit", help="fit the matrix from a RAW and an S-Log3 clip of the chart")
    f.add_argument("arw", type=Path)
    f.add_argument("clip", type=Path)
    f.add_argument("--gamut", default="SGamut3Cine", choices=sorted(V.RGB_TO_XYZ))
    f.add_argument("--seconds", type=float, default=1.0, help="video frames to average")
    f.add_argument("--photo-scale", type=int, default=4)
    f.add_argument("--out", type=Path, default=Path("sensor_matrix.json"))
    a = ap.parse_args()
    if a.cmd == "chart":
        a.out.write_text(chart_html())
        print(f"wrote {a.out}")
    else:
        fit_command(a)


if __name__ == "__main__":
    main()
