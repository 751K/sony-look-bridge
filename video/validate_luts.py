#!/usr/bin/env python3
"""Independent read-back check of written video LUTs with colour-science.

usage: validate_luts.py DIR [DIR ...]   (writes DIR/validation.json)

Checks per directory: file hashes and row counts; colour-science's tetrahedral
interpolation of the .cube against this project's interpolator; Sony gamut ->
ACES matrices against colour-science; and the S-Gamut3 vs S-Gamut3.Cine LUT of
each look on the same scene colours.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import colour
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import video_color as V  # noqa: E402

COLOUR_NAMES = {"SGamut3": "S-Gamut3", "SGamut3Cine": "S-Gamut3.Cine"}


def table_of(lut):
    # colour reads .cube as table[R, G, B] already.
    return np.asarray(lut.table, np.float64)


def validate(directory):
    directory = Path(directory)
    rng = np.random.default_rng(20261107)
    probe = rng.uniform(0, 1, (20000, 3))
    files, tables = [], {}
    for path in sorted(directory.glob("*.cube")):
        lut = colour.read_LUT(str(path))
        table = table_of(lut)
        ours = V.tetrahedral(table, probe)
        theirs = colour.algebra.table_interpolation_tetrahedral(probe, table)
        files.append({"name": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                      "row_count": int(np.prod(table.shape[:3])),
                      "independent_interpolator_max_abs_error": float(np.abs(ours - theirs).max())})
        parts = path.name.split("_")      # SonyA7M5_SLog3_<gamut>_<look>_...
        tables[(parts[2], parts[3])] = table
    aces = colour.RGB_COLOURSPACES["ACES2065-1"]
    transforms = {}
    for name, cname in COLOUR_NAMES.items():
        reference = colour.matrix_RGB_to_RGB(colour.RGB_COLOURSPACES[cname], aces, "CAT02")
        transforms[name] = {"matrix_max_abs_error": float(np.abs(reference - V.GAMUT_TO_ACES[name]).max())}
    # Same scene colours (inside both gamuts, -6..+5 stops) through both input versions.
    rec709 = V.rgb_to_xyz_matrix([[0.64, 0.33], [0.30, 0.60], [0.15, 0.06]])
    scene = rng.uniform(0.01, 1, (12000, 3)) @ rec709.T * 2.0 ** rng.uniform(-6, 5, (12000, 1))
    codes = {g: V.slog3_encode(scene @ np.linalg.inv(V.RGB_TO_XYZ[g]).T) for g in COLOUR_NAMES}
    ok = np.all([(c >= 0) & (c <= 1) for c in codes.values()], axis=(0, 2))
    cross = {}
    for look in sorted({k[1] for k in tables}):
        if ("SGamut3", look) in tables and ("SGamut3Cine", look) in tables:
            a = V.tetrahedral(tables[("SGamut3", look)], codes["SGamut3"][ok])
            b = V.tetrahedral(tables[("SGamut3Cine", look)], codes["SGamut3Cine"][ok])
            e = np.abs(a - b) * 255
            cross[look] = {"samples": int(ok.sum()), "mae_8bit": float(e.mean()),
                           "p99_8bit": float(np.percentile(e, 99))}
    report = {"independent_library": f"colour-science {colour.__version__}", "files": files,
              "input_transforms": transforms, "cross_gamut": cross}
    (directory / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    worst = max(f["independent_interpolator_max_abs_error"] for f in files)
    print(f"{directory}: {len(files)} files, interpolator max error {worst:.2e}, "
          f"cross-gamut MAE " + ", ".join(f"{k} {v['mae_8bit']:.2f}" for k, v in cross.items()))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for d in sys.argv[1:]:
        validate(d)
