"""Capture One's profile-input encoding E with the Linear Response curve (A7M5), and its inverse.

Capture One 16.8 feeds the input ICC from CImgOpApplyExposure. At camera defaults (exposure and
saturation 0) with the Linear Response film curve, the steps between white-balanced camera RGB x
(0..1 of the raw range) and the ICC input v are:

    ExposureCurve2012   per channel: g x below t = 0.5 / g, a rational shoulder through (1, 1) above
    film curve          Linear Response is the identity
    EvenTone            pulls the per channel result back towards the original hue (cross channel)
    ApplyGamma          1.075 sqrt(y) - 0.075, linear below y = 0.01947

The parameters (g = 1.11, EvenTone a = 0.5, b = 0.35) do not depend on the film curve chosen. EvenTone
only acts where the shoulder bends one channel more than another, i.e. once the brightest channel is
above t = 0.45; below that E is per channel and agrees with the chart probe calibration
(c1_encoding_table.json) to about 0.001. Sony linear camera RGB = x * SONY_PER_X.
"""
import numpy as np

GAIN = 1.11                  # ExposureCurve2012 gain
EVEN_A, EVEN_B = 0.5, 0.35   # EvenTone chroma floor and per-channel mix
SONY_PER_X = 8428.0          # Sony linear value at Capture One's x = 1
LUMA = np.array([0.299, 0.587, 0.114])

_T = 0.5 / GAIN
_C = 1.0 - _T
_S = 2.0 * GAIN * _C


def exposure_curve(x):
    d = x - _T
    return np.where(x < _T, GAIN * x, 0.5 * _S * d / (_C + (_S - 1.0) * d) + 0.5)


def exposure_curve_inverse(y):
    y = np.minimum(y, 0.5 + 0.45 * _S / (_S - 1.0))      # stay below the shoulder's pole
    u = y - 0.5
    return np.where(y < 0.5, y / GAIN, _T + u * _C / (0.5 * _S - (_S - 1.0) * u))


def _sqrt_encode(x):
    return np.where(x > 1 / 4096, np.sqrt(np.maximum(x, 0)) * (128 / 127) - 1 / 127, x * (4096 / 127))


def _sqrt_decode(y):
    return np.where(y > 1 / 127, ((y + 1 / 127) * (127 / 128)) ** 2, y * (127 / 4096))


def even_tone(curved, original):
    """EvenTone: the original colour at the curved colour's luma (Rec. 601, sqrt-like encoding), its chroma
    scaled by k = a + (1 - a) * (curved chroma / original chroma), softly compressed into [0, 1], decoded and
    mixed with the per channel result: b * curved + (1 - b) * hue preserving."""
    c, o = _sqrt_encode(curved), _sqrt_encode(original)
    luma = np.abs(np.minimum(c, 1) @ LUMA) + 1e-10
    c = c * (luma / (np.abs(c @ LUMA) + 1e-10))[..., None]
    o = o * (luma / (np.abs(o @ LUMA) + 1e-10))[..., None]
    k = EVEN_A + (1 - EVEN_A) * (c.max(-1) - c.min(-1) + 1e-6) / (o.max(-1) - o.min(-1) + 1e-6)
    out = luma[..., None] + (o - luma[..., None]) * k[..., None]
    excess = out.max(-1) - luma
    over = (1 - luma) < 2 * excess
    t = np.where(excess > 0, (1 - luma) / np.where(excess != 0, excess, 1), 1.0)
    u = np.maximum(1 - np.abs(t - 1), 0)
    s = np.minimum(t, 1) - u ** 3 / 6
    out = np.where(over[..., None], luma[..., None] + (out - luma[..., None]) * s[..., None], out)
    return EVEN_B * curved + (1 - EVEN_B) * _sqrt_decode(out)


def gamma(y):
    return np.where(y > 0.01947, np.sqrt(np.maximum(y, 0)) * 1.075 - 0.075, np.maximum(y, 0) * 3.8521)


def gamma_inverse(v):
    v = np.maximum(v, 0)
    return np.where(v > 0.075, ((v + 0.075) / 1.075) ** 2, v / 3.8521)


def encode(x):
    """White-balanced camera RGB x (..., 3), 0..1 of the raw range -> ICC input v."""
    x = np.asarray(x, np.float64)
    return gamma(even_tone(exposure_curve(x), x))


def decode(v, fixed_point=20, newton=30):
    """ICC input v (..., 3) -> x with encode(x) = v, and the residual max |encode(x) - v|.

    Starts from the per channel inverse, refines with a fixed point iteration and then damped Newton steps
    (numerical Jacobian, step halved until the residual does not grow). Every v that Capture One can produce
    is solved to ~1e-15. Some extreme nodes (one channel near 0, another bright) lie outside E's range; they
    keep the closest x found, and only enter rendering through interpolation next to reachable cells."""
    v = np.asarray(v, np.float64)
    target = exposure_curve_inverse(gamma_inverse(v))
    x = target.copy()
    for _ in range(fixed_point):
        x = np.maximum(x + target - exposure_curve_inverse(even_tone(exposure_curve(x), x)), 0)
    eye, h = np.eye(3), 1e-7
    for _ in range(newton):
        f = encode(x) - v
        err = np.abs(f).max(-1)
        J = np.stack([(encode(x + h * eye[k]) - encode(np.maximum(x - h * eye[k], 0))) /
                      (x + h * eye[k] - np.maximum(x - h * eye[k], 0))[..., k:k + 1] for k in range(3)], -1)
        step = np.linalg.solve(J + 1e-12 * eye, f[..., None])[..., 0]
        lam = np.ones(err.shape)
        for _ in range(10):
            xn = np.maximum(x - lam[..., None] * step, 0)
            ok = np.abs(encode(xn) - v).max(-1) <= err
            if ok.all():
                break
            lam = np.where(ok, lam, lam / 2)
        x = np.where(ok[..., None], xn, x)
    return x, np.abs(encode(x) - v).max(-1)


def node_sony_linear(grid, shaper):
    """Sony linear camera RGB (g, g, g, 3) at the ICC CLUT nodes, node coordinate s = v ** shaper
    (first index = R, ICC order)."""
    v1 = (np.arange(grid) / (grid - 1)) ** (1 / shaper)
    v = np.stack(np.meshgrid(v1, v1, v1, indexing="ij"), -1)
    x, _ = decode(v)
    return x * SONY_PER_X
