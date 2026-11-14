#!/usr/bin/env python3
"""README figure: the camera's own HEIF against this repository's decoder on a ColorChecker.

Input DIR (from a measurement run, not in the repository):
  results.json            {"DSC0xxxx": {"light", "look", "de": [50 ΔE2000 values], ...}}, the
                          24 ColorChecker Classic patches first, then 26 patches of the Passport's
                          other page; decoder = sonylook/sony_decode.decode with the camera
                          defaults, camera = the HEIF written with the same shot
  DSC0xxxx_{cam,dec}_crop.npy   ColorChecker page crops (sRGB 0..1) of the ST frames
Top: ST at each light, every patch split down the middle (left camera, right decoder).  The shots
differ in exposure (the 2600K one is about half a stop darker in the camera's own HEIF), so each
chart is scaled in linear light, both halves alike, until its white patch matches WHITE_L; this is
for display only, the ΔE values come from the unscaled data.
Bottom: mean ΔE2000 over the 50 patches for every look and light.
usage: make_chart_comparison.py DIR [OUT_DIR]   (writes compare_chart_{en,zh}.png)
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_CJK = "/System/Library/Fonts/Hiragino Sans GB.ttc"
FONT_LATIN = "/System/Library/Fonts/Helvetica.ttc"
BG, INK, MUTED, ACCENT, RULE = "#F5F5F1", "#202721", "#737B74", "#9C6134", "#D9D9D2"
W, M, GAP = 3000, 84, 30
CW = (W - 2 * M - 2 * GAP) // 3
LIGHTS = ("2600K", "4200K", "6500K")
LOOKS = ("ST", "PT", "NT", "VV", "VV2", "FL", "IN", "SH", "BW", "SE", "FL2", "FL3")
# Patch centres in the crop (full-resolution px): ColorChecker grid of patches.py minus the crop origin.
CROP_ORIGIN = (3150, 500)                      # x, y
SCALE = 7008 / 1400
XS = [688, 776, 863, 952]
YS = [208, 297, 385, 475, 565, 655]
HALF = 150                                     # half patch side drawn from the decoder, full px
WHITE_L = 92.0                                 # display lightness of the white patch (CIE L*)
COPY = {
    "zh": dict(title="相机直出与解码器对照", sub="α7 V · ST", table="各外观色差 ΔE2000"),
    "en": dict(title="Camera vs decoder", sub="α7 V · ST", table="Colour difference ΔE2000"),
}


def font(size, bold=False, cjk=False):
    return ImageFont.truetype(FONT_CJK if cjk else FONT_LATIN, size, index=1 if bold else 0)


def srgb_decode(v):
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def srgb_encode(v):
    v = np.clip(v, 0, 1)
    return np.where(v <= 0.0031308, v * 12.92, 1.055 * v ** (1 / 2.4) - 0.055)


def white_gain(cam):
    """Linear gain that brings the brightest ColorChecker patch of the camera crop to WHITE_L."""
    y = []
    for x in XS:
        for yy in YS:
            cx, cy = round(x * SCALE) - CROP_ORIGIN[0], round(yy * SCALE) - CROP_ORIGIN[1]
            rgb = srgb_decode(cam[cy - HALF // 2:cy + HALF // 2, cx - HALF:cx].reshape(-1, 3)).mean(0)
            y.append(rgb @ (0.2126, 0.7152, 0.0722))
    target = ((WHITE_L + 16) / 116) ** 3
    return target / max(y)


def split_chart(cam, dec):
    """Camera crop with the right half of every ColorChecker patch taken from the decoder."""
    g = white_gain(cam)
    cam, dec = (srgb_encode(srgb_decode(a) * g) for a in (cam, dec))
    out = cam.copy()
    for x in XS:
        for y in YS:
            cx = round(x * SCALE) - CROP_ORIGIN[0]
            cy = round(y * SCALE) - CROP_ORIGIN[1]
            out[cy - HALF:cy + HALF, cx:cx + HALF] = dec[cy - HALF:cy + HALF, cx:cx + HALF]
            out[cy - HALF:cy + HALF, cx - 3:cx + 3] = 0.12          # seam between the two halves
    return Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8))


def make(data, language, out):
    copy = COPY[language]
    res = json.loads((data / "results.json").read_text())
    st = {r["light"]: k for k, r in res.items() if r["look"] == "ST"}
    table = {(r["light"], r["look"]): float(np.mean(r["de"])) for r in res.values()}
    sample = np.load(data / f"{st[LIGHTS[0]]}_cam_crop.npy")
    ph = round(CW * sample.shape[0] / sample.shape[1])
    first = 230                                  # width of the light column
    cell_w = (W - 2 * M - first) // len(LOOKS)
    row_h = 120
    top = 200
    table_top = top + 90 + ph + 120
    H = table_top + 110 + row_h * (len(LIGHTS) + 1) + M
    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas)

    def label(x, y, text, size=48, fill=INK, bold=False, align="left"):
        cjk = any("　" <= c <= "鿿" for c in text)
        face = font(size, bold=bold, cjk=cjk)
        if align == "right":
            x -= draw.textlength(text, font=face)
        elif align == "center":
            x -= draw.textlength(text, font=face) / 2
        draw.text((x, y), text, font=face, fill=fill, anchor="lt")

    label(M, 60, copy["title"], 88, bold=True)
    label(W - M, 72, copy["sub"], 72, MUTED, bold=True, align="right")
    for i, light in enumerate(LIGHTS):
        x = M + i * (CW + GAP)
        cam = np.load(data / f"{st[light]}_cam_crop.npy")
        dec = np.load(data / f"{st[light]}_dec_crop.npy")
        label(x, top, light, 64, bold=True)
        label(x + CW, top, f"{table[light, 'ST']:.2f}", 64, ACCENT, bold=True, align="right")
        canvas.paste(split_chart(cam, dec).resize((CW, ph), Image.Resampling.LANCZOS), (x, top + 90))

    label(M, table_top, copy["table"], 72, bold=True)
    y0 = table_top + 110
    for j, look in enumerate(LOOKS):
        label(M + first + j * cell_w + cell_w / 2, y0 + 32, look, 56, bold=True, align="center")
    worst = max(table.values())
    for i, light in enumerate(LIGHTS):
        y = y0 + row_h * (i + 1)
        draw.line([(M, y), (W - M, y)], fill=RULE, width=2)
        label(M, y + 30, light, 60, bold=True)
        for j, look in enumerate(LOOKS):
            v = table[light, look]
            t = min(v / max(worst, 1.0), 1.0)
            fill = tuple(int(a + (b - a) * t * 0.55) for a, b in zip((245, 245, 241), (156, 97, 52)))
            x = M + first + j * cell_w
            draw.rectangle([x + 6, y + 10, x + cell_w - 6, y + row_h - 10], fill=fill)
            label(x + cell_w / 2, y + 30, f"{v:.2f}", 56, INK, align="center")
    path = out / f"compare_chart_{language}.png"
    canvas.save(path, optimize=True)
    return path


def main():
    data = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent
    for language in ("zh", "en"):
        print(make(data, language, out))


if __name__ == "__main__":
    main()
