"""Read the visible CFA raw from a Sony ARW through rawpy."""
from __future__ import annotations

import numpy as np

def read_raw(path):
    """Return `raw_image_visible` and validate the RGGB mosaic expected below."""
    import rawpy
    rggb = "only RGGB sensors are wired through the full pipeline"
    with rawpy.imread(str(path)) as r:
        assert r.color_desc == b"RGBG", rggb
        assert r.raw_pattern.tolist() == [[0, 1], [3, 2]], rggb
        return np.array(r.raw_image_visible, np.uint16, copy=True)
