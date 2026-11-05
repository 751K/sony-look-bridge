"""Render a minimal bilingual comparison from measure_comparison.py output.

usage: compare_figure_editorial.py MEASUREMENTS.json OUTPUT_DIRECTORY
Measurement definitions and display ranges belong in the README, not on the image.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageCms, ImageDraw, ImageFont, PngImagePlugin

REPORT_PATH = Path(sys.argv[1]).resolve()
DATA = REPORT_PATH.parent
REPORT = json.loads(REPORT_PATH.read_text())
OUT = Path(sys.argv[2]).resolve()
OUT.mkdir(parents=True, exist_ok=True)
FONT_CJK = '/System/Library/Fonts/Hiragino Sans GB.ttc'
FONT_LATIN = '/System/Library/Fonts/Helvetica.ttc'
BG, INK, MUTED, ACCENT = '#F5F5F1', '#202721', '#737B74', '#9C6134'
W, H = 3000, 3880
M, GAP, CW = 84, 30, 924
COLS = [M + i * (CW + GAP) for i in range(3)]
ERROR_W = (W - 2 * M - GAP) // 2
ERROR_H = ERROR_W * 2 // 3
ERROR_COLS = [M, M + ERROR_W + GAP]
NAMES = ('edit', 'c1', 'acr')
HEADERS = ('Sony Edit', 'Capture One', 'Camera Raw')
COPY = {
    'zh': {'title': 'Sony ST 外观对照', 'detail': '局部',
           'lightness': '明度误差', 'chromaticity': '色度误差'},
    'en': {'title': 'Sony ST look comparison', 'detail': 'Detail',
           'lightness': 'Lightness difference', 'chromaticity': 'Chromaticity difference'},
}


def font(size, bold=False, cjk=False):
    return ImageFont.truetype(FONT_CJK if cjk else FONT_LATIN, size, index=1 if bold else 0)


def make(language):
    copy = COPY[language]
    canvas = Image.new('RGB', (W, H), BG)
    draw = ImageDraw.Draw(canvas)

    def label(x, y, text, size=48, fill=INK, bold=False, align='left'):
        cjk = any('\u3000' <= char <= '\u9fff' for char in text)
        face = font(size, bold=bold, cjk=cjk)
        if align == 'right':
            x -= draw.textlength(text, font=face)
        draw.text((x, y), text, font=face, fill=fill, anchor='lt')

    def panel(path, x, y, width, height):
        with Image.open(path) as image:
            canvas.paste(image.convert('RGB').resize((width, height), Image.Resampling.LANCZOS), (x, y))

    label(M, 60, copy['title'], 76, bold=True)
    label(W - M, 78, 'α7 V · ST', 48, MUTED, align='right')

    for x, name, header in zip(COLS, NAMES, HEADERS):
        label(x, 184, header, 48, bold=True)
        panel(DATA / f'{name}_overview.png', x, 252, CW, 616)
        rx, ry, rw, rh = REPORT['method']['roi_xywh']
        full_h, full_w = REPORT['reference']['shape'][:2]
        box = (x + round(rx * CW / full_w), 252 + round(ry * 616 / full_h),
               x + round((rx + rw) * CW / full_w), 252 + round((ry + rh) * 616 / full_h))
        draw.rectangle(box, outline='#F4D8A7', width=3)

    label(M, 920, copy['detail'], 54, bold=True)
    for x, name in zip(COLS, NAMES):
        panel(DATA / f'{name}_detail.png', x, 1000, CW, 462)

    # Two full-width columns replace the old explanatory cards and small overlays.
    for metric, heading_y, header_y, image_y in (
        ('lightness', 1540, 1620, 1696),
        ('chromaticity', 2706, 2786, 2862),
    ):
        label(M, heading_y, copy[metric], 56, bold=True)
        for x, name, header in zip(ERROR_COLS, NAMES[1:], HEADERS[1:]):
            label(x, header_y, header, 46, bold=True)
            value = REPORT['hosts'][name][f'mean_{metric}_error']
            label(x + ERROR_W, header_y, f'{value:.2f}', 46, ACCENT, align='right')
            panel(DATA / f'{name}_{metric}.png', x, image_y, ERROR_W, ERROR_H)

    metadata = PngImagePlugin.PngInfo()
    metadata.add_text('Description', json.dumps({
        'measured_at': REPORT['measured_at'], 'box_reduction': 8, 'sscs': True,
        'components': {name: {metric: REPORT['hosts'][name][f'mean_{metric}_error']
                              for metric in ('lightness', 'chromaticity')} for name in NAMES[1:]},
        'map_max': REPORT['method']['error_maps']['display_max'],
    }))
    icc = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    destination = OUT / f'compare_ST_{language}.png'
    canvas.save(destination, pnginfo=metadata, icc_profile=icc, optimize=True)
    print(destination, canvas.size)


if __name__ == '__main__':
    for locale in ('zh', 'en'):
        make(locale)
