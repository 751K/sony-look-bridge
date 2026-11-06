"""Scene-linear transforms for S-Log3 Creative Look LUTs.

S-Log3 and gamut primaries: Sony Technical Summary, appendix, pp. 6–7:
https://pro.sony/s3/cms-static-content/uploadfile/06/1237494271406.pdf
Matrices use column vectors; arrays of RGB rows multiply their transpose.
"""
from __future__ import annotations

import numpy as np

WHITE_XY = np.array([0.3127, 0.3290])
WHITE_XYZ = np.array([WHITE_XY[0], WHITE_XY[1], 1 - WHITE_XY.sum()]) / WHITE_XY[1]
PRIMARIES = {
    "SGamut3": np.array([[0.730, 0.280], [0.140, 0.855], [0.100, -0.050]]),
    "SGamut3Cine": np.array([[0.766, 0.275], [0.225, 0.800], [0.089, -0.087]]),
}


def rgb_to_xyz_matrix(primaries, white_xy=WHITE_XY):
    xy = np.asarray(primaries, np.float64)
    xyz = np.column_stack((xy[:, 0], xy[:, 1], 1 - xy.sum(axis=1))) / xy[:, 1, None]
    basis = xyz.T
    w = np.array([*white_xy, 1 - np.sum(white_xy)]) / white_xy[1]
    return basis * np.linalg.solve(basis, w)[None, :]


RGB_TO_XYZ = {name: rgb_to_xyz_matrix(p) for name, p in PRIMARIES.items()}
SRGB_TO_XYZ = rgb_to_xyz_matrix([[.64, .33], [.30, .60], [.15, .06]])
AP0_WHITE = np.array([.32168, .33767])
AP0_TO_XYZ = rgb_to_xyz_matrix([[.7347, .2653], [0., 1.], [.0001, -.077]], AP0_WHITE)
# Same CAT02 white adaptation as Sony's ACES CTL; no camera calibration here.
CAT02 = np.array([[.7328, .4296, -.1624], [-.7036, 1.6975, .0061], [.0030, .0136, .9834]])
AP0_WHITE_XYZ = np.array([*AP0_WHITE, 1 - AP0_WHITE.sum()]) / AP0_WHITE[1]
D65_TO_D60 = np.linalg.inv(CAT02) @ np.diag((CAT02 @ AP0_WHITE_XYZ) / (CAT02 @ WHITE_XYZ)) @ CAT02
SRGB_TO_ACES = np.linalg.inv(AP0_TO_XYZ) @ D65_TO_D60 @ SRGB_TO_XYZ
ACES_TO_SRGB = np.linalg.inv(SRGB_TO_ACES)
GAMUT_TO_ACES = {name: np.linalg.inv(AP0_TO_XYZ) @ D65_TO_D60 @ matrix
                 for name, matrix in RGB_TO_XYZ.items()}


def slog3_decode(code):
    """Full-code normalized S-Log3 (10-bit CV / 1023) -> scene reflection."""
    cv = np.asarray(code, np.float64) * 1023.0
    return np.where(cv >= 171.2102946929,
                    10.0 ** ((cv - 420.0) / 261.5) * 0.19 - 0.01,
                    (cv - 95.0) * 0.01125 / (171.2102946929 - 95.0))


def slog3_encode(scene):
    scene = np.asarray(scene, np.float64)
    log_part = (420.0 + np.log10(np.maximum((scene + 0.01) / 0.19, 1e-30)) * 261.5) / 1023.0
    linear_part = (scene * (171.2102946929 - 95.0) / 0.01125 + 95.0) / 1023.0
    return np.where(scene >= 0.01125, log_part, linear_part)


def log_to_aces(code, gamut):
    """Sony S-Log3 / S-Gamut3(.Cine) -> ACES2065-1 AP0, linear, CAT02."""
    return slog3_decode(code) @ GAMUT_TO_ACES[gamut].T


def positive_rgb(rgb, weights=None):
    """Desaturate negative linear RGB towards equal RGB while preserving the weighted
    luminance (default: sRGB Y)."""
    x = np.asarray(rgb, np.float64)
    w = SRGB_TO_XYZ[1] if weights is None else np.asarray(weights, np.float64)
    y = np.maximum(x @ w, 0)[..., None]
    low = x.min(axis=-1, keepdims=True)
    factor = np.minimum(np.divide(y, y - low, out=np.ones_like(y), where=low < 0), 1)
    return np.maximum(y + factor * (x - y), 0)


def highlight_shoulder(camera, start, limit):
    """Compress maximum RGB smoothly, scaling all channels by the same factor.

    Identity through start; above it, slope starts at 1 and approaches limit.
    camera uses relative scene reflection, before Sony's integer scale.
    """
    if not 0 < start < limit:
        raise ValueError("highlight shoulder requires 0 < start < limit")
    rgb = np.maximum(np.asarray(camera, np.float64), 0.0)
    peak = rgb.max(axis=-1, keepdims=True)
    delta = np.maximum(peak - start, 0.0)
    mapped = np.where(peak <= start, peak, start + delta / (1 + delta / (limit - start)))
    return rgb * np.divide(mapped, peak, out=np.ones_like(peak), where=peak > 0)


def srgb_to_gamma24(code):
    """Preserve display light while moving sRGB code values to gamma 2.4."""
    s = np.clip(np.asarray(code, np.float64), 0, 1)
    linear = np.where(s <= 0.04045, s / 12.92, ((s + 0.055) / 1.055) ** 2.4)
    return linear ** (1 / 2.4)


def tetrahedral(table, rgb):
    """Interpolate a table indexed [R,G,B,channel] over the unit cube."""
    p = np.clip(rgb, 0, 1) * (len(table) - 1)
    i = np.minimum(p.astype(int), len(table) - 2)
    f = p - i
    order = np.argsort(-f, axis=-1, kind="stable")
    d1 = np.eye(3, dtype=int)[order[..., 0]]
    d2 = d1 + np.eye(3, dtype=int)[order[..., 1]]
    weights = np.take_along_axis(f, order, axis=-1)
    def at(delta):
        ix = i + delta
        return table[ix[..., 0], ix[..., 1], ix[..., 2]]
    c0, c1, c2, c3 = at(0), at(d1), at(d2), at(1)
    return (c0 + weights[..., 0, None] * (c1 - c0)
            + weights[..., 1, None] * (c2 - c1) + weights[..., 2, None] * (c3 - c2))
