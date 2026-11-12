#!/usr/bin/env python3
"""Build the per-camera Creative Look packs (one ZIP per camera, published as release assets).

Each pack holds the Capture One ICC profiles, the Camera Raw / Lightroom DCP + XMP profiles and the
DxO PhotoLab DCP + CUBE files for one camera, plus a 安装说明.md generated from
camera_packs/readme/template.md and camera_packs/readme/cameras.json.

Look parameters come from one sample ARW per camera (README of each pack names the source).
- Native looks use the sample's own look IFDs and SSCS parameters.
- Cameras without native FL2/FL3 get them from the α7 V sample (DSC03591): the camera's
  white-balanced RGB goes through SSCS (float path, the camera's parameters), then the camera-RGB
  conversion inv(FM2_A7M5) · FM2_camera from the Adobe Standard D65 ForwardMatrix, rows normalised to
  sum 1, then the α7 V look without SSCS.
- RGB2YCC blend weights: the camera writes them per shot from the white balance (0x7848, see
  docs/pipeline.md 4.3).  Every look is built twice: daylight (0, 1024, 0, 0) under the plain name
  and warm (1024, 0, 0, 0) with the suffix "Warm".  The warm correction set 0x7843 is zero on every
  body, so the warm variant is the base set alone.  Looks that render identically with both
  weights (BW) get no warm variant.  --as-shot builds one variant with each sample's own weights
  (this reproduces the v1.3.0 packs).
- Camera Raw also gets an "Auto" profile per colour look ("Look XX Auto"): one look table on a
  dual-illuminant base DCP whose HueSatMap follows the white balance, warm look at 3200K and below,
  daylight look at 5500K and above (camera_raw/acr_auto.py).  FL2 keeps the warm table and maps
  towards the daylight look, with a value axis.  Capture One and DxO have no equivalent.
- SSCS weights of 255 on all four CFA sites (α7S III, FX3 samples) are replaced by the default
  32/64/32.
- The software input calibration (Camera Raw, Capture One, DxO encodings) is the α7 V one.  For the
  other cameras the DxO highlight model uses the sample's as-shot white balance and the camera's
  Adobe D65 ForwardMatrix; α7 V keeps the constants measured on its own exports (dxo/dxo_model.py).

usage: build_packs.py SAMPLES_DIR OUT_DIR [--cameras Sony-A7-IV,...] [--as-shot]
SAMPLES_DIR holds the sample ARWs under the file names listed in CAMERAS.
"""
import argparse
import hashlib
import shutil
import sys
import zipfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for p in ("camera_raw", "capture_one", "dxo", "sonylook"):
    sys.path.insert(0, str(ROOT / p))
import acr_auto as AUTO  # noqa: E402
import acr_encoding as E  # noqa: E402
import acr_look as AL  # noqa: E402
import acr_profiles as A  # noqa: E402
import c1_look_profile as C  # noqa: E402
import dcp  # noqa: E402
import dxo_model as D  # noqa: E402
import dxo_profiles as P  # noqa: E402
import arw_looks as AW  # noqa: E402
from pack_notes import render_note  # noqa: E402
import sony_render as R  # noqa: E402
import sony_sscs as SC  # noqa: E402

ADOBE = Path("/Library/Application Support/Adobe/CameraRaw/CameraProfiles/Adobe Standard")
DAYLIGHT = (0, 1024, 0, 0)
WARM = (1024, 0, 0, 0)
PORTED = ("FL2", "FL3")
A7M5_SAMPLE = "Sony-A7-V-ILCE-7M5.ARW"

# stem, profile prefix, model (EXIF / Adobe), display name (Camera Raw group), sample file, native FL2/FL3
CAMERAS = [
    ("Sony-A1", "SonyA1", "ILCE-1", "Sony A1", "Sony-A1-ILCE-1.ARW", False),
    ("Sony-A1-II", "SonyA1M2", "ILCE-1M2", "Sony A1 II", "Sony-A1-II-ILCE-1M2.ARW", False),
    ("Sony-A6700", "SonyA6700", "ILCE-6700", "Sony A6700", "Sony-A6700-ILCE-6700.ARW", False),
    ("Sony-A7-IV", "SonyA7M4", "ILCE-7M4", "Sony A7 IV", "Sony-A7-IV-ILCE-7M4.ARW", False),
    ("Sony-A7-V", "SonyA7M5", "ILCE-7M5", "Sony A7M5", A7M5_SAMPLE, True),
    ("Sony-A7C-II", "SonyA7CM2", "ILCE-7CM2", "Sony A7C II", "Sony-A7C-II-ILCE-7CM2.ARW", False),
    ("Sony-A7CR", "SonyA7CR", "ILCE-7CR", "Sony A7CR", "Sony-A7CR-ILCE-7CR.ARW", False),
    ("Sony-A7R-V", "SonyA7RM5", "ILCE-7RM5", "Sony A7R V", "Sony-A7R-V-ILCE-7RM5.ARW", False),
    ("Sony-A7R-VI", "SonyA7RM6", "ILCE-7RM6", "Sony A7R VI", "Sony-A7R-VI-ILCE-7RM6.ARW", True),
    ("Sony-A7S-III", "SonyA7SM3", "ILCE-7SM3", "Sony A7S III", "Sony-A7S-III-ILCE-7SM3.ARW", False),
    ("Sony-A9-III", "SonyA9M3", "ILCE-9M3", "Sony A9 III", "Sony-A9-III-ILCE-9M3.ARW", False),
    ("Sony-FX2", "SonyFX2", "ILME-FX2", "Sony FX2", "Sony-FX2-ILME-FX2.ARW", True),
    ("Sony-FX3", "SonyFX3", "ILME-FX3", "Sony FX3", "Sony-FX3-ILME-FX3.ARW", False),
    ("Sony-FX30", "SonyFX30", "ILME-FX30", "Sony FX30", "Sony-FX30-ILME-FX30.ARW", False),
    ("Sony-RX1R-III", "SonyRX1RM3", "DSC-RX1RM3", "Sony RX1R III", "Sony-RX1R-III-DSC-RX1RM3.ARW", True),
    ("Sony-ZV-E1", "SonyZVE1", "ZV-E1", "Sony ZV-E1", "Sony-ZV-E1-ZV-E1.ARW", False),
    ("Sony-ZV-E10-II", "SonyZVE10M2", "ZV-E10M2", "Sony ZV-E10 II", "Sony-ZV-E10-II-ZV-E10M2.ARW", False),
]
XYZ_TO_PROPHOTO = np.linalg.inv(A.PROPHOTO_TO_XYZ)
DXO_DEFAULTS = {k: getattr(D, k) for k in ("K", "GAIN", "CLIP", "A", "A_INV")}


def adobe_standard(model):
    return dcp.read(ADOBE / f"Sony {model} Adobe Standard.dcp")


def sscs_params(arw):
    p = SC.params_from_arw(arw)
    if p["w"] == (255, 510, 255):
        p = dict(p, w=(32, 64, 32))
    return p


def fm2(model):
    a = adobe_standard(model)
    key = "ForwardMatrix2" if a["CalibrationIlluminant2"] == [21] else "ForwardMatrix1"
    return np.array(a[key], float).reshape(3, 3)


def set_dxo_model(arw, model):
    """DxO highlight model for this camera: sample's as-shot WB and the camera's D65 ForwardMatrix."""
    wb = [int(x) for x in str(AW.main_tags(arw)["0x7313"]).split()]
    gain = np.array([wb[0] / wb[1], 1.0, wb[3] / wb[1]])
    D.K = DXO_DEFAULTS["K"][1] * gain
    D.GAIN = gain
    D.CLIP = D.K * (16383 - D.BLACK)
    D.A = XYZ_TO_PROPHOTO @ fm2(model)
    D.A_INV = np.linalg.inv(D.A)


class Source:
    """Turns Sony-scale linear camera RGB of this camera into the look's input."""

    def __init__(self, look, pre=None):
        self.look, self.pre = look, pre

    def srgb(self, lin):
        return C.look_srgb(self.look, lin if self.pre is None else self.pre(lin))


def warm_differs(looks, name, sscs):
    """True when the warm and daylight weights render this look differently (False for BW)."""
    x = np.linspace(0, 1, 9)
    lin = np.stack(np.meshgrid(x, x, x, indexing="ij"), -1).reshape(-1, 3) ** 2.2 * 12000
    out = [C.look_srgb(R.Look(name, looks, sscs=sscs, ycc_weights=w), lin) for w in (DAYLIGHT, WARM)]
    return not np.array_equal(out[0], out[1])


def sources(arw, model, a7m5, weights, warm_only=False):
    """Look sources of one camera.  warm_only drops the looks whose warm variant renders the same
    as the daylight one."""
    looks = R.load_looks(arw)
    sscs = sscs_params(arw)
    native = {n: Source(R.Look(n, looks, sscs=sscs, ycc_weights=weights)) for n in C.NAMES
              if n in looks and not (warm_only and not warm_differs(looks, n, sscs))}
    if all(n in looks for n in PORTED):
        return native
    m = np.linalg.inv(fm2("ILCE-7M5")) @ fm2(model)
    m = m / m.sum(1, keepdims=True)
    m5 = R.load_looks(a7m5)

    def pre(lin):
        s = np.stack(SC.sscs_float(lin[..., 0], lin[..., 1], lin[..., 2], sscs), -1)
        return s @ m.T

    for n in PORTED:
        native[n] = Source(R.Look(n, m5, sscs=None, ycc_weights=weights), pre)
    return native


def tables(src):
    acr = AL.srgb_to_prophoto_v(src.srgb(np.minimum(E.inverse(A.grid(64)), E.CLIP)))
    s = np.arange(65) / 64
    lin1 = C.v_to_lin(s ** (1 / C.SHAPER))
    lin = np.stack(np.meshgrid(lin1, lin1, lin1, indexing="ij"), -1)
    c1 = C.srgb_to_lab_d50(src.srgb(lin))
    dxo = AL.srgb_to_prophoto_v(src.srgb(D.E_inv(P.grid(64))))
    return acr, c1, dxo


def build(cam, samples, out, as_shot=False):
    stem, prefix, model, group, sample, _ = cam
    arw = str(samples / sample)
    pack = out / f"{stem}-Creative-Looks"
    if pack.exists():
        shutil.rmtree(pack)
    acr_dir, c1_dir, dxo_dir = (pack / d for d in ("Adobe Camera Raw and Lightroom", "Capture One", "DxO PhotoLab"))
    for d in (acr_dir, c1_dir, dxo_dir):
        d.mkdir(parents=True)
    A.OUT, A.MODEL, A.PREFIX, A.GROUP = acr_dir, f"Sony {model}", prefix, group
    A.BASE_NAME, A.ADOBE_STD = f"{prefix} Linear Base", ADOBE / f"Sony {model} Adobe Standard.dcp"
    A.write_base()
    P.OUT, P.MODEL, P.ADOBE_STD = dxo_dir, f"Sony {model}", A.ADOBE_STD
    P.write_base2(f"{prefix} Linear Base v2")
    if model != "ILCE-7M5":          # α7 V keeps the DxO model constants measured on its own exports
        set_dxo_model(arw, model)
    try:
        variants = [("", None, False)] if as_shot else [("", DAYLIGHT, False), (" Warm", WARM, True)]
        srcs, acrs = {}, {}
        for suffix, weights, warm_only in variants:
            for name, src in sources(arw, model, str(samples / A7M5_SAMPLE), weights, warm_only).items():
                short = C.NAMES[name] + suffix
                acr, c1, dxo = tables(src)
                srcs[name, suffix], acrs[name, suffix] = src, acr
                A.write_look(f"Look {short}", acr)
                C.write_icc(c1_dir / f"{prefix}-Look-{short.replace(' ', '-')}.icc", f"{prefix} Look {short}", c1)
                P.write_cube(dxo_dir / f"{prefix} Look {short}.cube", dxo, f"{prefix} Look {short}")
                print(f"  {short}", flush=True)
        if not as_shot:
            write_auto(acr_dir, prefix, model, arw, srcs, acrs)
    finally:
        for k, v in DXO_DEFAULTS.items():
            setattr(D, k, v)
    (pack / "安装说明.md").write_text(
        render_note(stem, model, prefix, group), encoding="utf-8")
    return zip_pack(pack)


def write_auto(acr_dir, prefix, model, arw, srcs, acrs):
    """Camera Raw Auto profiles: base DCP with the fitted HueSatMap + XMP look table on it."""
    vmax = AUTO.vmax_from_arw(AW.main_tags(arw))
    base_name = A.BASE_NAME
    try:
        for name, suffix in list(srcs):
            if suffix != " Warm":
                continue
            day, warm = srcs[name, ""], srcs[name, " Warm"]
            direction, nv = ("day", 16) if name == "FL2" else ("warm", 1)
            table, target, key = (warm, day, " Warm") if direction == "day" else (day, warm, "")
            hsm, before, after = AUTO.fit_hsm(table.srgb, target.srgb, vmax, nv)
            short = C.NAMES[name]
            A.BASE_NAME = f"{prefix} Auto Base {short}"
            AUTO.write_base(acr_dir / f"{A.BASE_NAME}.dcp", A.MODEL, A.BASE_NAME, A.ADOBE_STD, hsm, direction)
            A.write_look(f"Look {short} Auto", acrs[name, key])
            print(f"  {short} Auto ({direction}, NV {nv}): fit residual ΔE76 {before:.2f} -> {after:.2f}", flush=True)
    finally:
        A.BASE_NAME = base_name


def zip_pack(pack):
    path = pack.with_suffix(".zip")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(pack.rglob("*")):
            if f.is_file():
                info = zipfile.ZipInfo(str(f.relative_to(pack.parent)), date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, f.read_bytes())
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("samples", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--cameras", help="comma-separated stems (default: all)")
    ap.add_argument("--as-shot", action="store_true",
                    help="one variant per look with each sample's own RGB2YCC blend weights")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    want = set(a.cameras.split(",")) if a.cameras else None
    zips = []
    for cam in CAMERAS:
        if want and cam[0] not in want:
            continue
        print(cam[0], flush=True)
        zips.append(build(cam, a.samples, a.out, a.as_shot))
    sums = a.out / "SHA256SUMS.txt"
    lines = {}
    if sums.exists():
        for line in sums.read_text().splitlines():
            h, n = line.split(maxsplit=1)
            lines[n.strip()] = h
    for z in zips:
        lines[z.name] = hashlib.sha256(z.read_bytes()).hexdigest()
    sums.write_text("".join(f"{lines[n]}  {n}\n" for n in sorted(lines)))
    print(sums)


if __name__ == "__main__":
    main()
