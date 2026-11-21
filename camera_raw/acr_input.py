"""Camera Raw's mapping from Sony linear camera RGB to the RGBTable input, from Camera Raw's own pipeline.

With the default base DCP, Camera Raw's total exposure E = BaselineExposure + log2(largest white balance
multiplier) is above 0, and Exposure2012 splits it into a linear gain and a highlight rolloff according
to the image's own statistics: the input of a fixed RGBTable changes from picture to picture. The base
DCP here carries a BaselineExposureOffset that keeps E at or below -1 for every white balance. Camera Raw
then uses a fixed path that depends neither on the picture nor on the white balance:

    ABCtoRGB      camera -> linear ProPhoto (identity for this base), with a soft colour limit: a
                  channel above a quarter of its own clip level is pulled towards the brighter channels
    exposure      linear gain 2^(E + 1)
    rgb_tone      curve T = clip(ProfileToneCurve(B(x))) on a 4097-point table, applied with RGBTone
                  (lo / hi pulled towards the middle channel, looked up, then solved back)
    RGBTable      input in ProPhoto gamma 1.8

B is Camera Raw's brightness curve for -1 stop, used in a gamma 2.2 encoding: a line of slope 1/2 up
to 0.25, then the inverse of a cubic Hermite to (1, 1). Relative to u = Sony linear / CLIP the gain is
K = 2^(BaselineExposure + offset + 1). The ProfileToneCurve makes T(K u) a soft clip,
g u / (1 + (g u)^p)^(1/p) with g = 1.4, p = 1.25: slope 1.4 in the shadows, 0.67 at the green clip level
(u = 1), so the table's nodes spread over the camera's range about as with the chart calibration.
Every channel can exceed u = 1 up to its own clip level (its white balance gain, up to about 3.5). Up to
u = 4 the kernel's solve-back must not clip: it looks the brightest channel up after pulling it towards
the middle one and extrapolates back, and a result above 1 is clipped, which also lowers the middle
channel. A curve that bends towards 1 too early (T(2) close to 1) clips there.

The soft colour limit depends on the white balance; the table inverts it at SOFT_LIMIT_WB (4600K), which
holds within about 0.3 ΔE2000 for highlights from 2600K to 7000K.

BASELINE_EXPOSURE lists the bodies whose Camera Raw BaselineExposure is known; other bodies keep the
chart calibration of acr_encoding.py on the base without an offset.
"""
import numpy as np
from scipy.interpolate import CubicSpline

CLIP = 0.515625 * (16383 - 512)            # Sony linear at the green sensor clip
BASELINE_EXPOSURE = {"ILCE-7M5": 0.35}     # Camera Raw's BaselineExposure (as written into its DNGs)
GAIN_EV = -3.15                            # BaselineExposure + offset + 1: E <= -1 up to log2 s = 2.15 + exposure
K = 2.0 ** GAIN_EV
SOFT_LIMIT_WB = np.array([2142, 1024, 1926]) / 1024.0    # Sony WB gains R, G, B at 4600K (α7 V)
TABLE_SIZE = 4096

_GAMMA = 2.2
_SLOPE = 2.0 ** (1 / _GAMMA)               # brightness curve part for 1 stop
_END_SLOPE = max(1.0 / ((_SLOPE - 1.0) * 12.0 + 1.0), 0.1)
_KNEE = 0.5 / _SLOPE
_WIDTH = 1.0 - _KNEE


def supported(model):
    return model in BASELINE_EXPOSURE


def offset(model):
    """BaselineExposureOffset for the base DCP of this body."""
    return GAIN_EV - 1.0 - BASELINE_EXPOSURE[model]


def _brightness_part(x):
    """cr_curve_brightness_part for 1 stop: line to (knee, 0.5), cubic Hermite to (1, 1)."""
    t = (x - _KNEE) / _WIDTH
    u = 1.0 - t
    hermite = (0.5 * (t + 2.0 - u) + t * _WIDTH * _SLOPE) * u * u + t * t * ((2.0 - t + u) - u * _WIDTH * _END_SLOPE)
    return np.where(x < _KNEE, x * _SLOPE, hermite)


_P_X = np.linspace(0.0, 1.0, 200001)
_P_Y = _brightness_part(_P_X)


def brightness_minus_one(x):
    """B(x) = P^-1(x^(1/2.2))^2.2 on [0, 1]."""
    x = np.clip(x, 0.0, 1.0)
    return np.interp(x ** (1 / _GAMMA), _P_Y, _P_X) ** _GAMMA


TONE_U = np.array([0, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 2, 2.75, 3.75, 5])    # control points in u, plus B = 1
TONE_G, TONE_P = 1.4, 1.25


def tone_target(u):
    gu = TONE_G * np.asarray(u, np.float64)
    return gu / (1 + gu ** TONE_P) ** (1 / TONE_P)


def tone_curve_points():
    """ProfileToneCurve control points (B(K u), tone_target(u)) and (1, 1). The natural spline through them
    stays within 0.008 of the target and rises strictly well beyond u = 4."""
    pts = np.c_[brightness_minus_one(K * TONE_U), tone_target(TONE_U)]
    return np.r_[pts, [[1.0, 1.0]]].astype(np.float32).astype(np.float64)


def _profile_tone_curve():
    p = tone_curve_points()
    return CubicSpline(p[:, 0], p[:, 1], bc_type="natural")


def tone_table():
    """The rgb_tone stage's table: T(i / 4096), i = 0..4096, plus a repeated last entry."""
    x = np.arange(TABLE_SIZE + 1) / TABLE_SIZE
    t = np.clip(_profile_tone_curve()(brightness_minus_one(x)), 0.0, 1.0)
    return np.r_[t, t[-1]]


_TABLE = tone_table()


def tone(x):
    s = np.clip(x, 0.0, 1.0) * TABLE_SIZE
    i = np.minimum(s.astype(np.int64), TABLE_SIZE)
    f = s - i
    return _TABLE[i] + f * (_TABLE[i + 1] - _TABLE[i])


_TOP = int(np.argmax(np.diff(_TABLE) <= 0))   # the curve rises strictly up to here (u > 5)


def tone_inverse(y):
    xs = np.arange(_TOP + 1) / TABLE_SIZE
    return np.interp(np.clip(y, 0.0, 1.0), _TABLE[:_TOP + 1], xs)


def _order(rgb):
    hi, lo = rgb.max(-1), rgb.min(-1)
    mid = rgb.sum(-1) - hi - lo
    span = hi - lo
    t = np.where(span > 0, (mid - lo) / np.where(span > 0, span, 1.0), 0.0)
    return hi, mid, lo, t


def _place(rgb, lo, mid, hi):
    order = np.argsort(rgb, -1, kind="stable")
    out = np.empty_like(rgb)
    np.put_along_axis(out, order, np.stack([lo, mid, hi], -1), -1)
    return out


def rgb_tone(rgb):
    """SIMDLinearToneSDR_32 with the pre-mix flag (Camera Raw's rgb_tone kernel)."""
    hi, mid, lo, t = _order(rgb)
    h = hi + (mid - hi) * t * t / 2
    l = lo + (mid - lo) * (1 - t) ** 2 / 2
    Hp, Lp = tone(h), tone(l)
    d = 1 / (t * t - t + 2)
    H = np.clip(d * ((t - 1) * t * t * Lp - (t ** 3 - 2 * t * t + t - 2) * Hp), 0, 1)
    L = np.clip(d * ((t ** 3 - t * t + 2) * Lp - t * (t - 1) ** 2 * Hp), 0, 1)
    return _place(rgb, L, L + t * (H - L), H)


def rgb_tone_inverse(out):
    hi, mid, lo, t = _order(out)
    a11, a12 = -(t ** 3 - 2 * t * t + t - 2), (t - 1) * t * t
    a21, a22 = -t * (t - 1) ** 2, t ** 3 - t * t + 2
    det = (a11 * a22 - a12 * a21) / (t * t - t + 2)
    h = tone_inverse((a22 * hi - a12 * lo) / det)
    l = tone_inverse((a11 * lo - a21 * hi) / det)
    p, q = (1 - t) * t * t / 2, t * (1 - t) ** 2 / 2         # h = (1 - p) HI + p LO,  l = q HI + (1 - q) LO
    det2 = (1 - p) * (1 - q) - p * q
    HI = ((1 - q) * h - p * l) / det2
    LO = ((1 - p) * l - q * h) / det2
    return _place(out, LO, LO + t * (HI - LO), HI)


def soft_limit(u, w=SOFT_LIMIT_WB):
    """ABCtoRGB's soft colour limit in Sony units (channel i clips at u = w_i); slots by gain, largest first."""
    order = np.argsort(-w, kind="stable")
    c, ww = u[..., order], w[order]
    t = np.clip((c / ww - 0.25) / 0.75, 0, 1) ** 2        # 1 at a channel's own clip level
    m = np.maximum(c[..., 0], c[..., 1])
    c0 = c[..., 0] + (m - c[..., 0]) * t[..., 0]
    c1 = c[..., 1] + (m - c[..., 1]) * t[..., 1]
    m2 = np.maximum((c0 + c1) / 2, c[..., 2])
    c2 = c[..., 2] + (m2 - c[..., 2]) * t[..., 2]
    out = np.empty_like(u)
    out[..., order[0]], out[..., order[1]], out[..., order[2]] = c0, c1, c2
    return out


def _pull_inverse(y, m, w, iterations=60):
    """Solve c + (m - c) t(c / w) = y for c in [0, y] by bisection (y <= m)."""
    lo, hi = np.zeros_like(y), y.copy()
    for _ in range(iterations):
        c = (lo + hi) / 2
        t = np.clip((c / w - 0.25) / 0.75, 0, 1) ** 2
        big = c + (m - c) * t > y
        hi, lo = np.where(big, c, hi), np.where(big, lo, c)
    return (lo + hi) / 2


def soft_limit_inverse(y, w=SOFT_LIMIT_WB):
    """Inverse of soft_limit: of the first two slots the larger is unchanged and the smaller was pulled towards
    it; the third slot was pulled towards the mean of the first two (results)."""
    order = np.argsort(-w, kind="stable")
    c, ww = np.asarray(y, np.float64)[..., order], w[order]
    c0, c1, c2 = c[..., 0], c[..., 1], c[..., 2]
    m = np.maximum(c0, c1)
    u0 = np.where(c0 < m, _pull_inverse(c0, m, ww[0]), c0)
    u1 = np.where(c1 < m, _pull_inverse(c1, m, ww[1]), c1)
    m2 = (c0 + c1) / 2
    u2 = np.where(c2 < m2, _pull_inverse(np.minimum(c2, m2), m2, ww[2]), c2)
    out = np.empty_like(c)
    out[..., order[0]], out[..., order[1]], out[..., order[2]] = u0, u1, u2
    return out


def forward(lin, w=SOFT_LIMIT_WB):
    """Sony linear RGB (..., 3) -> RGBTable input (ProPhoto gamma 1.8)."""
    u = np.asarray(lin, np.float64) / CLIP
    return np.clip(rgb_tone(K * soft_limit(u, w)), 0, None) ** (1 / 1.8)


def inverse(v, w=SOFT_LIMIT_WB):
    """RGBTable input (..., 3) -> Sony linear RGB (the look chain itself clips at 16383)."""
    x = rgb_tone_inverse(np.clip(np.asarray(v, np.float64), 0, 1) ** 1.8)
    return soft_limit_inverse(x / K, w) * CLIP


# --- per body: new path where BaselineExposure is known, chart calibration otherwise ---------------------

def _exif_model(unique_camera_model):
    return unique_camera_model.removeprefix("Sony ")


def base_entries(unique_camera_model):
    """DCP entries that set up the RGBTable input for this body (ProfileToneCurve, BaselineExposureOffset)."""
    model = _exif_model(unique_camera_model)
    if not supported(model):
        return [("ProfileToneCurve", 11, [0.0, 0.0, 1.0, 1.0])]
    return [("ProfileToneCurve", 11, tone_curve_points().ravel().tolist()),
            ("BaselineExposureOffset", 10, [offset(model)])]


def table_to_linear(unique_camera_model, v):
    """RGBTable input -> Sony linear RGB for this body's base DCP."""
    if supported(_exif_model(unique_camera_model)):
        return inverse(v)
    import acr_encoding
    return np.minimum(acr_encoding.inverse(v), acr_encoding.CLIP)


def linear_to_table(unique_camera_model, lin):
    if supported(_exif_model(unique_camera_model)):
        return forward(lin)
    import acr_encoding
    return acr_encoding.forward(lin)
