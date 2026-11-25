#!/usr/bin/env python3
"""Auto profiles for Camera Raw / Lightroom: one look that follows the white balance.

Sony cameras blend two RGB2YCC parameter sets of each look by the as-shot white balance (on the α7 V
with a Kelvin white balance: warm set at 4100K and below, daylight set at 5400K and above, linear in
mired between; docs/pipeline.md 4.3).  A Camera Raw
XMP profile holds one look table, but its base DCP can be dual-illuminant, and Camera Raw interpolates
the DCP's HueSatMap between the two calibration illuminants by the white balance (in mired).

The base DCP 'PREFIX Auto Base XX.dcp' is the Linear Base (ForwardMatrix = ProPhoto -> XYZ D50, so
linear ProPhoto is the white-balanced camera RGB) with
- CalibrationIlluminant1/2 = cool white fluorescent (4150K in the DNG SDK) / D55 (5500K), the
  standard pair closest to the camera's transition (about 4000K-5100K as Camera Raw reads it),
- ColorMatrix1/2 = the camera's Adobe Standard StdA / D65 matrices interpolated in mired to those
  temperatures, so white balance between 4150K and 5500K reads as with Adobe Standard,
- a HueSatMap (90 hue x 30 saturation x NV value; DNG order value, hue, saturation; linear value
  encoding) at one illuminant and identity at the other.

The XMP 'PREFIX Look XX Auto' holds one of the two looks; the HueSatMap moves its input so that the
result matches the other look:
- direction "warm" (default): the table is the daylight look, HueSatMap1 (4150K) maps to the warm look;
- direction "day": the table is the warm look, HueSatMap2 (5500K) maps to the daylight look.  FL2
  needs this: its warm look reaches saturated yellows that the daylight table cannot output, while the
  reverse (removing saturation) is reachable.  FL2 also gets a 16-level value axis.

The HueSatMap is fitted per cell (hue shift in degrees, saturation scale, value scale) by
Gauss-Newton on the CIELAB residual between table_look(map(x)) and target_look(x), with x at each
cell's own hue / saturation and at several exposures (2D) or at the cell's value (3D).  The neutral
axis (saturation 0) is left unchanged.  The value axis is indexed by the pixel's maximum channel
relative to the raw white level, which is what Camera Raw sees before exposure: v = Sony linear /
vmax_from_arw(arw).

Bodies other than the α7 V raise the daylight weight above 1024 at high colour temperatures (A7 IV
library: 1024 up to about 5390K camera temperature, then linear in mired to 1348 at about 6420K).  For
them write_base_triple makes a triple-illuminant base (DNG 1.6, IlluminantData lights): warm look,
daylight look and the daylight look at weight 1348.  Camera Raw weights the three maps by inverse
squared distance in (min(1500 / T, 1), 0.005 * tint) with a smoothstep (CalculateTripleIlluminantWeights),
not linearly in mired; the light positions are fitted on 2500 A7 IV library shots (camera 0x7848 against
their Camera Raw temperature and tint), which lowers the weight error from 0.46 (dual, no 1348 state) to
0.10 rms.

The same mechanism cannot carry the α7 V fluorescent set (0x7845): Fluor.CoolWhite sits at about 4200K
/ +43 tint in Camera Raw, only 20-25 tint units from ordinary shots in the warm-daylight transition, so
any light placement leaks 0.1-0.3 fluorescent weight into them (4200K chart 0.50 -> 0.75 ΔE2000).  The
α7 V gets separate fluorescent profiles instead (camera_packs/build_packs.py).
"""
import struct

import numpy as np

import acr_input
import dcp

NH, NS = 90, 30
T1, T2 = 4150.0, 5500.0
ILL1, ILL2 = 14, 20                     # EXIF LightSource: cool white fluorescent, D55
ILLUMINANT_K = {17: 2850.0, 21: 6500.0, 20: 5500.0, 23: 5000.0, 24: 3200.0, 14: 4150.0}   # dng_camera_profile::IlluminantToTemperature
# Triple-illuminant lights as (temperature for the ColorMatrix, CIE xy of the IlluminantData): warm /
# daylight / daylight at weight 1348, DNG temperature / tint (4070K, +19), (5170K, +22), (6550K, +18),
# fitted on the A7 IV library.
DAY_RAMP_LIGHTS = ((4070.0, (0.381608, 0.391190)), (5170.0, (0.341416, 0.363312)), (6550.0, (0.311268, 0.333005)))
CAL3, CM3, FM3, HSM3 = 52529, 52531, 52532, 52537          # DNG 1.6 tags
ILLUMINANT_DATA = (52533, 52534, 52535)
OTHER = 255
WHITE = 4000.0                          # Sony linear value of diffuse white
EXPOSURES = (0.06, 0.15, 0.35, 0.7)     # x WHITE, value (max channel) of the 2D fit samples
PROPHOTO_TO_XYZ = np.array([[0.7976749, 0.1351917, 0.0313534],
                            [0.2880402, 0.7118741, 0.0000857],
                            [0.0, 0.0, 0.8252100]])


def vmax_from_arw(main_tags):
    """Sony linear value of the raw white level 0x787f in the green channel (ZcTaskITP scaling)."""
    t = lambda k: [int(v) for v in str(main_tags[k]).split()]
    g = t("0x7313")[1] * int(main_tags.get("0x7809", 256)) / 256      # 256 when absent (older bodies)
    return int(main_tags["0x7311"]) / 32768 * g * 0.0625 * (t("0x787f")[1] - t("0x7310")[1])


# --- HSV as in the DNG SDK (hue in [0, 6)) ---
def rgb_to_hsv(rgb):
    r, g, b = np.moveaxis(rgb, -1, 0)
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = mx - mn
    s = np.where(mx > 0, d / np.where(mx > 0, mx, 1), 0)
    dd = np.where(d > 0, d, 1)
    h = np.where(mx == r, (g - b) / dd, np.where(mx == g, 2 + (b - r) / dd, 4 + (r - g) / dd))
    h = np.where(d > 0, h % 6, 0)
    return h, s, mx


def hsv_to_rgb(h, s, v):
    h = h % 6
    i = np.floor(h).astype(int); f = h - i
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    sel = [np.stack(c, -1) for c in ((v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q))]
    out = np.zeros(h.shape + (3,))
    for k in range(6):
        m = (i % 6) == k
        out[m] = sel[k][m]
    return out


def apply_hsm(rgb, table, vmax):
    """table (NH, NS, NV, 3): hue shift (deg), sat scale, val scale.  Linear interpolation in hue
    (wraps), saturation and value (v / vmax clamped to [0, 1]), as Camera Raw applies it."""
    nv = table.shape[2]
    h, s, v = rgb_to_hsv(rgb)
    hs = h * (NH / 6.0); si = s * (NS - 1)
    h0 = np.floor(hs).astype(int); fh = hs - h0; h0 %= NH; h1 = (h0 + 1) % NH
    s0 = np.minimum(np.floor(si).astype(int), NS - 2); fs = si - s0
    if nv > 1:
        vi = np.clip(v / vmax, 0, 1) * (nv - 1)
        v0 = np.minimum(np.floor(vi).astype(int), nv - 2); fv = vi - v0
    else:
        v0 = np.zeros_like(h0); fv = np.zeros_like(h)
    v1 = np.minimum(v0 + 1, nv - 1)
    e = 0
    for hi, wh in ((h0, 1 - fh), (h1, fh)):
        for sj, ws in ((s0, 1 - fs), (s0 + 1, fs)):
            for vk, wv in ((v0, 1 - fv), (v1, fv)):
                e = e + (wh * ws * wv)[..., None] * table[hi, sj, vk]
    return hsv_to_rgb(h + e[..., 0] * (6 / 360.0), np.minimum(s * e[..., 1], 1.0), v * e[..., 2])


def _lab(srgb):
    s = np.clip(srgb, 0, 1)
    lin = np.where(s <= 0.04045, s / 12.92, ((s + 0.055) / 1.055) ** 2.4)
    m = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])
    x = lin @ m.T / np.array([0.95047, 1, 1.08883])
    f = np.where(x > 0.008856, np.cbrt(x), 7.787 * x + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def fit_hsm(table_srgb, target_srgb, vmax, nv=1, iterations=25):
    """HueSatMap (NH, NS, nv, 3) with table_srgb(map(x)) ~ target_srgb(x).

    table_srgb / target_srgb: Sony-scale linear camera RGB (..., 3) -> sRGB 0..1.
    Returns (table, mean CIELAB residual over the fit samples before, after)."""
    H = np.arange(NH) * (6.0 / NH)
    S = np.arange(NS) / (NS - 1)
    if nv == 1:
        vals = np.array(EXPOSURES) * WHITE
        hh, ss, vv = (a[:, :, None, :] for a in np.meshgrid(H, S, vals, indexing="ij"))    # (NH, NS, 1, NE)
    else:
        vals = np.maximum(np.arange(nv) / (nv - 1), 0.25 / (nv - 1)) * vmax
        hh, ss, vv = (a[..., None] for a in np.meshgrid(H, S, vals, indexing="ij"))        # (NH, NS, NV, 1)
    src = hsv_to_rgb(hh, ss, vv)
    target = _lab(target_srgb(src.reshape(-1, 3))).reshape(src.shape)

    def resid(p):
        q = p[..., None, :]
        x = hsv_to_rgb(hh + q[..., 0] * (6 / 360.0), np.minimum(ss * q[..., 1], 1.0), vv * q[..., 2])
        return _lab(table_srgb(x.reshape(-1, 3))).reshape(target.shape) - target

    params = np.zeros((NH, NS, nv, 3)); params[..., 1:] = 1.0
    steps = np.array([0.5, 0.01, 0.01])
    lam = 1e-2
    before = float(np.linalg.norm(resid(params), axis=-1).mean())
    for _ in range(iterations):
        r0 = resid(params)
        J = np.stack([(resid(params + np.eye(3)[k] * steps[k]) - r0) / steps[k] for k in range(3)], -1)
        Jm = J.reshape(NH, NS, nv, -1, 3)
        rv = r0.reshape(NH, NS, nv, -1)
        A = np.einsum("hsvrk,hsvrl->hsvkl", Jm, Jm) + lam * np.eye(3)
        g = np.einsum("hsvrk,hsvr->hsvk", Jm, rv)
        delta = -np.linalg.solve(A, g[..., None])[..., 0]
        delta[..., 0] = np.clip(delta[..., 0], -10, 10)
        delta[..., 1:] = np.clip(delta[..., 1:], -0.2, 0.2)
        trial = params + delta
        trial[..., 1:] = np.clip(trial[..., 1:], 0.3, 3)
        better = np.square(resid(trial)).sum((-1, -2)) < np.square(r0).sum((-1, -2))
        params = np.where(better[..., None], trial, params)
        lam = lam * (0.5 if better.mean() > 0.5 else 2)
    params[:, 0] = [0, 1, 1]
    after = float(np.linalg.norm(resid(params), axis=-1).mean())
    return params, before, after


def _cm_at(cm1, cm2, t1, t2, T):
    w = np.clip((1 / T - 1 / t2) / (1 / t1 - 1 / t2), 0, 1)
    return w * cm1 + (1 - w) * cm2


def write_base(path, model, name, adobe_std, table, direction="warm"):
    """Dual-illuminant base DCP with the fitted HueSatMap at 4150K (warm) or 5500K (day)."""
    a = dcp.read(adobe_std)
    cm1, cm2 = (np.array(a[k], float).reshape(3, 3) for k in ("ColorMatrix1", "ColorMatrix2"))
    t1, t2 = ILLUMINANT_K[a["CalibrationIlluminant1"][0]], ILLUMINANT_K[a["CalibrationIlluminant2"][0]]
    nv = table.shape[2]
    fit = table.transpose(2, 0, 1, 3).astype(np.float32)          # DNG order: value, hue, saturation
    ident = np.zeros_like(fit); ident[..., 1:] = 1.0
    hsm1, hsm2 = (fit, ident) if direction == "warm" else (ident, fit)
    dcp.write(path, [
        ("UniqueCameraModel", 2, model), ("ProfileName", 2, name),
        ("ColorMatrix1", 10, _cm_at(cm1, cm2, t1, t2, T1)), ("ColorMatrix2", 10, _cm_at(cm1, cm2, t1, t2, T2)),
        ("CalibrationIlluminant1", 3, [ILL1]), ("CalibrationIlluminant2", 3, [ILL2]),
        ("ForwardMatrix1", 10, PROPHOTO_TO_XYZ), ("ForwardMatrix2", 10, PROPHOTO_TO_XYZ),
        ("ProfileHueSatMapDims", 4, [NH, NS, nv]),
        ("ProfileHueSatMapData1", 11, hsm1.reshape(-1)), ("ProfileHueSatMapData2", 11, hsm2.reshape(-1)),
        ("ProfileHueSatMapEncoding", 4, [0]),
        *acr_input.base_entries(model), ("ProfileEmbedPolicy", 4, [0]),
        ("DefaultBlackRender", 4, [1]), ("ProfileCopyright", 2, "Sony Look Bridge (not an Adobe profile)")])
    return path


def _illuminant_data(xy):
    """IlluminantData: type 0 (CIE xy) followed by two URATIONAL."""
    return list(struct.pack("<HIIII", 0, round(xy[0] * 1e6), 1000000, round(xy[1] * 1e6), 1000000))


def write_base_triple(path, model, name, adobe_std, maps, lights=DAY_RAMP_LIGHTS):
    """Triple-illuminant base DCP.  maps: HueSatMaps (NH, NS, NV, 3) at the three lights, None for
    identity (the light whose look the XMP table holds)."""
    a = dcp.read(adobe_std)
    cm1, cm2 = (np.array(a[k], float).reshape(3, 3) for k in ("ColorMatrix1", "ColorMatrix2"))
    t1, t2 = ILLUMINANT_K[a["CalibrationIlluminant1"][0]], ILLUMINANT_K[a["CalibrationIlluminant2"][0]]
    cms = [_cm_at(cm1, cm2, t1, t2, T) for T, _ in lights]
    nv = next(m.shape[2] for m in maps if m is not None)
    ident = np.zeros((NH, NS, nv, 3), np.float32); ident[..., 1:] = 1.0
    data = [(ident if m is None else m).transpose(2, 0, 1, 3).astype(np.float32).reshape(-1) for m in maps]
    dcp.write(path, [
        ("UniqueCameraModel", 2, model), ("ProfileName", 2, name),
        ("ColorMatrix1", 10, cms[0]), ("ColorMatrix2", 10, cms[1]), (CM3, 10, cms[2]),
        ("CalibrationIlluminant1", 3, [OTHER]), ("CalibrationIlluminant2", 3, [OTHER]), (CAL3, 3, [OTHER]),
        *[(tag, 7, _illuminant_data(xy)) for tag, (_, xy) in zip(ILLUMINANT_DATA, lights)],
        ("ForwardMatrix1", 10, PROPHOTO_TO_XYZ), ("ForwardMatrix2", 10, PROPHOTO_TO_XYZ), (FM3, 10, PROPHOTO_TO_XYZ),
        ("ProfileHueSatMapDims", 4, [NH, NS, nv]),
        ("ProfileHueSatMapData1", 11, data[0]), ("ProfileHueSatMapData2", 11, data[1]), (HSM3, 11, data[2]),
        ("ProfileHueSatMapEncoding", 4, [0]),
        *acr_input.base_entries(model), ("ProfileEmbedPolicy", 4, [0]),
        ("DefaultBlackRender", 4, [1]), ("ProfileCopyright", 2, "Sony Look Bridge (not an Adobe profile)")])
    return path
