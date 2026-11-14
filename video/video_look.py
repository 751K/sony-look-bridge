#!/usr/bin/env python3
"""Build A7M5 S-Log3 / S-Gamut3(.Cine) -> Creative Look -> Rec.709 gamma 2.4 LUTs.

Video is mapped back to white-balanced camera RGB with a measured sensor matrix (calibration/) and
then runs through the photo look chain.  Both depend on the white balance, so the LUTs come in three
variants, each with the ColorChecker matrix fitted at its light and the camera's look state there:
  Daylight (no suffix)  6500K matrix, RGB2YCC / LinearMatrix16 weights 0 1024 0 0
  4200K    (-4200K)     4200K matrix, weights 644 380 0 0 (the camera's at that light)
  Warm     (-Warm)      2600K matrix, weights 1024 0 0 0 (warm LinearMatrix16 tables)

usage: video_look.py A7M5.ARW --write --eval
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for p in (HERE, ROOT / "sonylook"):
    sys.path.insert(0, str(p))
import sony_render as R  # noqa: E402
import sony_sscs as SC  # noqa: E402
import video_color as V  # noqa: E402

CALIBRATION = HERE / "calibration" / "A7M5_SGamut3Cine_chart_6500K.json"
# variant: (file-name suffix, calibration file, RGB2YCC / LinearMatrix16 blend weights)
VARIANTS = {
    "Daylight": ("", HERE / "calibration" / "A7M5_SGamut3Cine_chart_6500K.json", (0, 1024, 0, 0)),
    "4200K": ("-4200K", HERE / "calibration" / "A7M5_SGamut3Cine_chart_4200K.json", (644, 380, 0, 0)),
    "Warm": ("-Warm", HERE / "calibration" / "A7M5_SGamut3Cine_chart_2600K.json", (1024, 0, 0, 0)),
}
# Default exposure: S-Log3 shot at +1 2/3 EV over the meter.
EXPOSURE = -1.667
# Sony's hue-index luminance weights (LM16 hue calculation), used for camera-space gamut handling.
SONY_LUMA = np.array([109., 366., 37.]) / 512


class SensorBridge:
    """Measured video gamut -> white-balanced camera RGB (sensor_calibration.py fit)."""

    def __init__(self, path):
        self.path = Path(path)
        self.data = json.loads(self.path.read_text())
        measured = self.data["gamut"]
        self.matrix = np.asarray(self.data["matrix"], np.float64)
        self.from_aces_matrix = self.matrix @ np.linalg.inv(V.GAMUT_TO_ACES[measured])

    def camera_from_aces(self, aces):
        return np.asarray(aces, np.float64) @ self.from_aces_matrix.T


NAMES = {"Standard": "ST", "Vivid": "VV", "Neutral": "NT", "Portrait": "PT",
         **{n: n for n in ("FL", "VV2", "IN", "SH", "FL2", "FL3", "BW", "Sepia")}}
ALL_LOOKS = "ST,PT,NT,VV,VV2,FL,IN,SH,BW,Sepia,FL2,FL3"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def look_srgb(look, camera):
    shape = camera.shape
    planes = np.clip(camera.reshape(-1, 1, 3), 0, 16383).astype(np.float32)
    return look.render(planes, pointwise=True).reshape(shape).astype(float) / 16383


def neutral_value(look, value):
    return float(look_srgb(look, np.full((1, 3), value))[0].mean())


def neutral_input(look, target):
    lo, hi = 0.0, 16383.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if neutral_value(look, mid) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def calibrate(standard, scale):
    """scale: Sony native camera value per unit S-Log3 scene reflection at equal metering.
    Returns it with the highlight shoulder limit, ST's near-white input in scene units."""
    limit = neutral_input(standard, 0.999) / scale
    return scale, limit


def render_aces(look, aces, bridge, scale, limit, exposure=0.0):
    """Linear AP0 -> camera RGB (measured matrix) -> photo look chain -> Rec.709 gamma 2.4."""
    camera = bridge.camera_from_aces(aces) * (2. ** exposure)
    camera = V.highlight_shoulder(V.positive_rgb(camera, SONY_LUMA), .9, limit) * scale
    return V.srgb_to_gamma24(look_srgb(look, camera))


def render(look, code, gamut, bridge, scale, limit, exposure=0.0):
    return render_aces(look, V.log_to_aces(code, gamut), bridge, scale, limit, exposure)


def build(look, n, gamut, bridge, scale, limit, exposure=0.0):
    axis = np.linspace(0, 1, n)
    grid = np.stack(np.meshgrid(axis, axis, axis, indexing="ij"), axis=-1)
    return render(look, grid, gamut, bridge, scale, limit, exposure)


def write_cube(path, values, title, note="measured sensor matrix; photo look chain on camera RGB"):
    n = len(values)
    # .cube: red changes fastest; internal table is [R,G,B,channel].
    rows = values.transpose(2, 1, 0, 3).reshape(-1, 3)
    if values.shape != (n, n, n, 3) or not np.isfinite(values).all():
        raise ValueError("LUT must be a finite n x n x n x 3 array")
    if values.min() < 0 or values.max() > 1:
        raise ValueError("display LUT output must be within 0..1")
    with Path(path).open("w", newline="\n") as f:
        f.write(f'TITLE "{title}"\n')
        f.write("# Input: S-Log3, full-code normalized (10-bit CV / 1023)\n")
        f.write("# Output: Rec.709 primaries, display gamma 2.4\n")
        f.write(f"# {note}\n")
        f.write(f"LUT_3D_SIZE {n}\nDOMAIN_MIN 0 0 0\nDOMAIN_MAX 1 1 1\n")
        np.savetxt(f, rows, fmt="%.9f")


# Toned looks shift hue along the grey axis, so single channels need not rise monotonically.
TONED = {"Sepia"}


def evaluate(look, table, gamut, bridge, scale, limit, exposure=0.0, toned=False):
    rng = np.random.default_rng(20261106)
    # Physical colours: Rec.709 primaries, scene exposures -6..+6 stops.
    rec_matrix = V.rgb_to_xyz_matrix([[0.64, 0.33], [0.30, 0.60], [0.15, 0.06]])
    scene = rng.uniform(0.01, 1, (12000, 3)) * (2.0 ** rng.uniform(-6, 6, (12000, 1)))
    sg = scene @ (np.linalg.inv(V.RGB_TO_XYZ[gamut]) @ rec_matrix).T
    code = V.slog3_encode(sg)
    code = code[np.all((code >= 0) & (code <= 1), axis=1)]
    ref = render(look, code, gamut, bridge, scale, limit, exposure)
    got = V.tetrahedral(table, code)
    error = np.abs(got - ref) * 255
    stops = np.array([-8, -6, -4, -2, 0, 1, 2, 3, 4, 5, 6, 7], float)
    greys = np.repeat(V.slog3_encode(0.18 * 2.0 ** stops)[:, None], 3, axis=1)
    direct_grey = render(look, greys, gamut, bridge, scale, limit, exposure)
    cube_grey = V.tetrahedral(table, greys)
    dense_grey = np.repeat(np.linspace(95 / 1023, 1, 4096)[:, None], 3, axis=1)
    dense_result = V.tetrahedral(table, dense_grey)
    if toned:
        # Display-light luminance; allow Sony's integer rounding (~1e-4).
        y = (np.clip(dense_result, 0, 1) ** 2.4) @ V.rgb_to_xyz_matrix(
            [[0.64, 0.33], [0.30, 0.60], [0.15, 0.06]])[1]
        if np.any(np.diff(y) < -1e-4):
            raise ValueError("LUT grey ramp luminance is not monotone")
    elif np.any(np.diff(dense_result, axis=0) < -1e-9):
        raise ValueError("LUT neutral ramp is not monotone")
    return {
        "samples": len(code), "interpolation": "tetrahedral",
        "error_units": "8-bit Rec.709 gamma 2.4 code values",
        "mae": float(error.mean()), "p99": float(np.percentile(error, 99)),
        "max": float(error.max()), "neutral_ramp_monotone": True,
        "neutral_ramp_check": "luminance, 1e-4 tolerance" if toned else "every channel",
        "grey_stops": [{"ev": float(e), "direct": a.tolist(), "cube": b.tolist()}
                       for e, a, b in zip(stops, direct_grey, cube_grey)],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("arw", type=Path)
    ap.add_argument("--looks", default=ALL_LOOKS)
    ap.add_argument("--gamuts", default="SGamut3,SGamut3Cine")
    ap.add_argument("--grid", type=int, default=65)
    ap.add_argument("--exposure", type=float, default=EXPOSURE,
                    help="scene exposure offset in stops (default -1.667: S-Log3 shot at +1 2/3 EV)")
    ap.add_argument("--out", type=Path, default=ROOT / "profiles/video")
    ap.add_argument("--variants", default=",".join(VARIANTS),
                    help="LUT variants: " + ", ".join(VARIANTS))
    ap.add_argument("--sensor-matrix", type=Path,
                    help="calibration JSON (matrix and sony_scale) for every variant instead of each "
                         "variant's own chart calibration")
    ap.add_argument("--sony-scale", type=float,
                    help="override the calibration's Sony native value per unit S-Log3 scene reflection")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--eval", action="store_true")
    a = ap.parse_args()
    if a.grid < 2:
        ap.error("--grid must be at least 2")
    if not np.isfinite(a.exposure) or abs(a.exposure) > 20:
        ap.error("--exposure must be within -20..20 stops")
    names = {**{n: n for n in NAMES}, **{short: n for n, short in NAMES.items()}}
    requested = a.looks.split(",")
    gamuts = a.gamuts.split(",")
    variants = a.variants.split(",")
    if any(n not in names for n in requested) or any(g not in V.RGB_TO_XYZ for g in gamuts):
        ap.error("unknown look or gamut; gamuts: SGamut3,SGamut3Cine")
    if any(v not in VARIANTS for v in variants):
        ap.error("unknown variant; variants: " + ",".join(VARIANTS))
    looks = R.load_looks(str(a.arw))
    if looks["_main"]["SonyModelID"] != 407:
        ap.error("an A7M5 ARW is required")
    sscs = SC.params_from_arw(a.arw)
    report = {
        "camera": "Sony ILCE-7M5", "grid": a.grid,
        "input": "S-Log3, full-code normalized; gamut identified per LUT",
        "output": "Rec.709 primaries / display gamma 2.4, normalized 0..1",
        "bridge": "measured video gamut -> A7M5 white-balanced camera RGB matrix, then the photo look chain",
        "working_encoding": "ACES2065-1 AP0 linear; Sony gamut conversion with CAT02 D65/D60 adaptation",
        "gamut_handling": "negative camera RGB desaturated to equal RGB at Sony hue-index luminance",
        "calibration": "measured Sony scale at equal photo / S-Log3 metering (ISO-normalised pairs)",
        "exposure_ev": a.exposure, "sscs": sscs,
        "source_arw": {"name": a.arw.name, "sha256": sha256(a.arw)},
        "edit_arm64_sha256": R._edit_sha(),
        "generator_sha256": {p.name: sha256(p) for p in (HERE / "video_look.py", HERE / "video_color.py",
                                                         ROOT / "sonylook" / "sony_render.py",
                                                         ROOT / "sonylook" / "warm_780f.json")},
        "variants": {}, "files": [],
    }
    if a.write:
        a.out.mkdir(parents=True, exist_ok=True)
    for variant in dict.fromkeys(variants):
        suffix, calibration, weights = VARIANTS[variant]
        calibration = a.sensor_matrix or calibration
        bridge = SensorBridge(calibration)
        sony_scale = a.sony_scale if a.sony_scale is not None else bridge.data.get("sony_scale")
        if sony_scale is None or not 0 < sony_scale < 1e6:
            ap.error("a positive Sony scale is required (calibration sony_scale or --sony-scale)")
        standard = R.Look("Standard", looks, sscs=sscs, ycc_weights=weights)
        scale, limit = calibrate(standard, sony_scale)
        if limit <= 0.9:
            raise ValueError("ST white point must be above the 90% shoulder start")
        report["variants"][variant] = {
            "suffix": suffix, "ycc_weights": list(weights), "sony_scale": scale,
            "highlight_shoulder": {"start": 0.9, "limit": limit, "method": "maximum-RGB rational shoulder"},
            "sensor_matrix": {"file": calibration.name, "sha256": sha256(calibration),
                              "gamut": bridge.data["gamut"], "matrix": bridge.matrix.tolist()}}
        for name in dict.fromkeys(names[n] for n in requested):
            look = standard if name == "Standard" else R.Look(name, looks, sscs=sscs, ycc_weights=weights)
            for gamut in dict.fromkeys(gamuts):
                short = NAMES[name] + suffix
                filename = f"SonyA7M5_SLog3_{gamut}_{short}_Rec709_G24_{a.grid}.cube"
                table = build(look, a.grid, gamut, bridge, scale, limit, a.exposure)
                entry = {"name": filename, "look": NAMES[name], "variant": variant, "gamut": gamut,
                         "fade": R.CAMERA_FADE.get(name, 0)}
                if a.eval:
                    entry["evaluation"] = evaluate(look, table, gamut, bridge, scale, limit, a.exposure,
                                                   toned=name in TONED)
                if a.write:
                    path = a.out / filename
                    write_cube(path, table, f"Sony A7M5 S-Log3 {gamut} {short} to Rec709 Gamma 2.4",
                               f"{variant} variant; chart sensor matrix; photo look chain on camera RGB")
                    entry["sha256"] = sha256(path)
                report["files"].append(entry)
                print(filename + (f'  MAE {entry["evaluation"]["mae"]:.3f}' if a.eval else ""), flush=True)
        print(f"{variant}: Sony scale {scale:.6f}; shoulder 0.9 -> {limit:.6f}")
    if a.write:
        (a.out / "manifest.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
