#!/usr/bin/env python3
"""Measure three real TIFF exports and prepare lossless panels for the editorial figure.

usage: measure_comparison.py EDIT.tif C1.tif ACR.tif OUTPUT_DIRECTORY [--reuse-registration]
Uses the existing cubic registration and colour-space conversion, in bounded row strips.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import tifffile
from PIL import Image

import compare_acr_export as C
import compare_c1_export as X
import sony_render as R

FACTOR = 8
# Lit brickwork, cloud texture and warm sky, avoiding the near-black foreground.
ROI = (3500, 1400, 1752, 876)
LAB_MAP_MAX = 4.0
CHROMA_DISPLAY_L = 65.0
CHROMA_DISPLAY_GAIN = 15.0


def srgb_to_lab(rgb):
    """CIELAB relative to the sRGB D65 white, from unquantized encoded sRGB."""
    rgb = np.clip(np.asarray(rgb, dtype=np.float64), 0, 1)
    linear = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    xyz = linear @ X.SRGB.T
    xyz /= np.array([0.95047, 1.0, 1.08883])
    delta = 6 / 29
    f = np.where(xyz > delta ** 3, np.cbrt(xyz), xyz / (3 * delta ** 2) + 4 / 29)
    return np.stack([116 * f[..., 1] - 16,
                     500 * (f[..., 0] - f[..., 1]),
                     200 * (f[..., 1] - f[..., 2])], axis=-1)


def lab_to_linear_srgb(lab):
    lab = np.asarray(lab, dtype=np.float64)
    fy = (lab[..., 0] + 16) / 116
    f = np.stack([fy + lab[..., 1] / 500, fy, fy - lab[..., 2] / 200], axis=-1)
    delta = 6 / 29
    xyz = np.where(f > delta, f ** 3, 3 * delta ** 2 * (f - 4 / 29))
    xyz *= np.array([0.95047, 1.0, 1.08883])
    return xyz @ np.linalg.inv(X.SRGB).T


def chromaticity_residual(delta_lab, valid):
    """Signed a*,b* residual on neutral L*=65; chroma is amplified equally for both hosts."""
    ab = np.asarray(delta_lab[..., 1:], dtype=np.float64)
    magnitude = np.linalg.norm(ab, axis=-1)
    ab = ab * (CHROMA_DISPLAY_GAIN * np.minimum(1, LAB_MAP_MAX / np.maximum(magnitude, 1e-20)))[..., None]
    lab = np.concatenate([np.full((*ab.shape[:-1], 1), CHROMA_DISPLAY_L), ab], axis=-1)
    linear = lab_to_linear_srgb(lab)
    outside = np.any((linear < 0) | (linear > 1), axis=-1)
    # Compress only out-of-gamut chroma, retaining the residual's Lab hue direction and L*.
    if outside.any():
        points = lab[outside].copy()
        low, high = np.zeros(len(points)), np.ones(len(points))
        for _ in range(14):
            mid = (low + high) / 2
            trial = points.copy()
            trial[:, 1:] *= mid[:, None]
            rgb = lab_to_linear_srgb(trial)
            inside = np.all((rgb >= 0) & (rgb <= 1), axis=-1)
            low = np.where(inside, mid, low)
            high = np.where(inside, high, mid)
        points[:, 1:] *= low[:, None]
        linear[outside] = lab_to_linear_srgb(points)
    linear = np.clip(linear, 0, 1)
    encoded = np.where(linear <= 0.0031308, 12.92 * linear,
                       1.055 * linear ** (1 / 2.4) - 0.055)
    return np.where(valid[..., None], encoded, 0.1)


def error_map_description():
    return {"display_max": LAB_MAP_MAX,
            "lightness": "linear grayscale; black at 0, white at 4 or above",
            "chromaticity": {"kind": "signed a*,b* residual; host minus reference",
                             "neutral_L": CHROMA_DISPLAY_L, "chroma_gain": CHROMA_DISPLAY_GAIN,
                             "magnitude_cap": LAB_MAP_MAX,
                             "gamut": "chroma compression at fixed L* and Lab hue; no per-host normalization"}}


def source_info(path):
    path = Path(path)
    with tifffile.TiffFile(path) as t:
        page = t.pages[0]
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        result = {"file": path.name, "sha256": digest,
                  "shape": list(page.shape), "dtype": str(page.dtype)}
        for key in ("Software", "DateTime"):
            if key in page.tags:
                result[key] = page.tags[key].value
    return result


def sample(img, cx, cy, shape, sign, factor=8):
    """Bilinear warp into Edit coordinates; reduce only after sampling at full resolution."""
    H, W = shape
    h, w = img.shape[:2]
    out = np.zeros((H // factor, W // factor, 3), np.float32)
    valid = np.zeros(out.shape[:2], bool)
    rx, ry, rw, rh = ROI
    crop = np.zeros((rh, rw, 3), np.float32)
    x = np.arange(W, dtype=np.float64)
    for y0 in range(0, H, 128):
        y1 = min(y0 + 128, H)
        yy, xx = np.meshgrid(np.arange(y0, y1), x, indexing="ij")
        b = C.basis(xx, yy, W, H)
        sx, sy = xx + sign * (b @ cx), yy + sign * (b @ cy)
        v = (sx >= 0) & (sx <= w - 2) & (sy >= 0) & (sy <= h - 2)
        ix = np.clip(np.floor(sx).astype(int), 0, w - 2)
        iy = np.clip(np.floor(sy).astype(int), 0, h - 2)
        fx, fy = (sx - ix)[..., None], (sy - iy)[..., None]
        row = (img[iy, ix] * (1-fx) * (1-fy) + img[iy, ix+1] * fx * (1-fy)
               + img[iy+1, ix] * (1-fx) * fy + img[iy+1, ix+1] * fx * fy)
        out[y0//factor:y1//factor] = R.box(row, factor)
        valid[y0//factor:y1//factor] = R.box(v[..., None].astype(np.float32), factor)[..., 0] == 1
        a, z = max(ry, y0), min(ry + rh, y1)
        if a < z:
            crop[a-ry:z-ry] = row[a-y0:z-y0, rx:rx+rw]
    return out, valid, crop


def save_rgb(path, a):
    Image.fromarray(np.rint(np.clip(a, 0, 1) * 255).astype(np.uint8)).save(path)


def main():
    ed_path, c1_path, acr_path, out_path = sys.argv[1:5]
    out = Path(out_path)
    out.mkdir(parents=True, exist_ok=True)
    previous = None
    if "--reuse-registration" in sys.argv[5:]:
        previous = json.loads((out / "measurements.json").read_text())
        assert previous["reference"]["sha256"] == source_info(ed_path)["sha256"]
    ed, ed_space = X.load(ed_path)
    ed = ed.astype(np.float32)
    H, W = ed.shape[:2]
    assert H % FACTOR == W % FACTOR == 0
    rx, ry, rw, rh = ROI
    assert rx + rw <= W and ry + rh <= H
    E = R.box(ed, FACTOR)
    arrays, masks, crops, hosts = [E], [], [ed[ry:ry+rh, rx:rx+rw]], {}
    for name, path in (("c1", c1_path), ("acr", acr_path)):
        print("Loading", name, flush=True)
        img, space = X.load(path)
        img = img.astype(np.float32)
        if previous is None:
            cx, cy, n, residual = C.fit_poly(img, ed)
            signs = (1, -1)
        else:
            old = previous["hosts"][name]
            assert old["source"]["sha256"] == source_info(path)["sha256"]
            cx, cy = np.array(old["displacement_x"]), np.array(old["displacement_y"])
            n, residual = old["fit_points"], old["fit_residual_px"]
            signs = (old["sign"],)
        best = None
        for sign in signs:
            a, m, crop = sample(img, cx, cy, (H, W), sign)
            mae = float(np.abs(a-E)[m].mean() * 255)
            print(name, "sign", sign, "MAE", mae, flush=True)
            if best is None or mae < best[0]:
                best = mae, sign, a, m, crop
        _, sign, a, m, crop = best
        arrays.append(a); masks.append(m); crops.append(crop)
        hosts[name] = {"source": source_info(path), "source_colour_space": space.strip(),
                       "fit_points": n, "fit_residual_px": residual, "sign": sign,
                       "displacement_x": cx.tolist(), "displacement_y": cy.tolist()}
        del img
    common = masks[0] & masks[1]
    assert common.mean() > 0.9, "Too little common coverage; inspect registration."
    np.savez_compressed(out / "registered_box8.npz", edit=E, c1=arrays[1], acr=arrays[2], valid=common)
    reference_lab = srgb_to_lab(E)
    names = ("edit", "c1", "acr")
    for name, a, crop in zip(names, arrays, crops):
        save_rgb(out / f"{name}_overview.png", np.where(common[..., None], a, 0.1))
        save_rgb(out / f"{name}_detail.png", crop)
        if name != "edit":
            d = (a-E) * 255
            hosts[name]["mae_box8"] = float(np.abs(d[common]).mean())
            hosts[name]["p95_absolute_channel_error"] = float(np.percentile(np.abs(d[common]), 95))
            error = np.clip(np.max(np.abs(d), axis=-1) * 8 / 255, 0, 1)
            error[~common] = 0.1
            save_rgb(out / f"{name}_error.png", np.repeat(error[..., None], 3, -1))
            delta_lab = srgb_to_lab(a) - reference_lab
            lightness = np.abs(delta_lab[..., 0])
            chromaticity = np.linalg.norm(delta_lab[..., 1:], axis=-1)
            for metric, values in (("lightness", lightness), ("chromaticity", chromaticity)):
                hosts[name][f"mean_{metric}_error"] = float(values[common].mean())
                hosts[name][f"p95_{metric}_error"] = float(np.percentile(values[common], 95))
                if metric == "chromaticity":
                    display = chromaticity_residual(delta_lab, common)
                else:
                    gray = np.where(common, np.clip(values / LAB_MAP_MAX, 0, 1), 0.1)
                    display = np.repeat(gray[..., None], 3, -1)
                save_rgb(out / f"{name}_{metric}.png", display)
    report = {"measured_at": datetime.now(timezone.utc).isoformat(),
              "look": "ST", "camera": "Sony ILCE-7M5", "sscs": True,
              "reference": source_info(ed_path), "reference_colour_space": ed_space.strip(),
              "method": {"units": "8-bit sRGB channel values", "box_reduction": FACTOR,
                         "registration": "Cubic displacement fitted to gradient phase correlations; bilinear sampling",
                         "mask": "Intersection of both host exports; all source pixels in each 8x8 block must be valid",
                         "common_blocks": int(common.sum()), "total_blocks": int(common.size),
                         "component_units": "CIELAB coordinate units; L* spans 0 to 100",
                         "lab_white": "D65 (Xn=0.95047, Yn=1, Zn=1.08883)",
                         "lab_conversion": "sRGB to CIELAB after the 8x8 encoded-sRGB box average; no intermediate 8-bit quantization",
                         "lightness_error": "abs(L*_host - L*_edit)",
                         "chromaticity_error": "sqrt((a*_host-a*_edit)^2 + (b*_host-b*_edit)^2); includes hue and chroma changes, excludes the L* component",
                         "error_maps": error_map_description(),
                         "roi_xywh": list(ROI),
                         "limitation": "One photograph and ST only. Edge residuals include geometry, demosaic and sharpening differences."},
              "hosts": hosts}
    if previous is not None:
        for key in ("configuration_evidence", "raw"):
            if key in previous:
                report[key] = previous[key]
    dest = out / "measurements.json"
    dest.write_text(json.dumps(report, indent=2) + "\n")
    print(dest, {name: round(item["mae_box8"], 4) for name, item in hosts.items()}, flush=True)


if __name__ == "__main__":
    main()
