#!/usr/bin/env python3
"""Read/write DNG Camera Profile (.dcp) files: TIFF-style 'IIRC' container with DNG profile tags.

The generators read only the matrices of Adobe's own camera profiles (ADOBE_FIELDS).
`dcp.py --export-adobe OUT.json DCP ...` writes those fields of the given profiles to one file; with
ADOBE_STANDARD_MATRICES=OUT.json, read() serves a profile of the same file name from it instead of the
disk, so the packs can be built without Camera Raw installed (the release workflow).  The file holds
Adobe data: keep it private, never commit it.
"""
import json
import os
import struct
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np

TAGS = {50708: "UniqueCameraModel", 50721: "ColorMatrix1", 50722: "ColorMatrix2", 50778: "CalibrationIlluminant1",
        50779: "CalibrationIlluminant2", 50936: "ProfileName", 50937: "ProfileHueSatMapDims",
        50938: "ProfileHueSatMapData1", 50939: "ProfileHueSatMapData2", 50940: "ProfileToneCurve",
        50941: "ProfileEmbedPolicy", 50942: "ProfileCopyright", 50964: "ForwardMatrix1", 50965: "ForwardMatrix2",
        50981: "ProfileLookTableDims", 50982: "ProfileLookTableData", 51107: "ProfileHueSatMapEncoding",
        51108: "ProfileLookTableEncoding", 51109: "BaselineExposureOffset", 51110: "DefaultBlackRender",
        50932: "ProfileCalibrationSignature"}
NAMES = {v: k for k, v in TAGS.items()}
TSIZE = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 7: 1, 9: 4, 10: 8, 11: 4, 12: 8}
TFMT = {1: "B", 7: "B", 3: "H", 4: "I", 9: "i", 11: "f", 12: "d"}


ADOBE_FIELDS = ("ColorMatrix1", "ColorMatrix2", "ForwardMatrix1", "ForwardMatrix2",
                "CalibrationIlluminant1", "CalibrationIlluminant2")


@lru_cache(maxsize=1)
def _adobe_file():
    path = os.environ.get("ADOBE_STANDARD_MATRICES")
    return json.loads(Path(path).read_text()) if path else None


def read(path):
    stored = _adobe_file()
    if stored is not None and Path(path).name in stored:
        return {k: list(v) for k, v in stored[Path(path).name].items()}
    b = open(path, "rb").read()
    assert b[:4] == b"IIRC", b[:4]
    off = struct.unpack_from("<I", b, 4)[0]
    n = struct.unpack_from("<H", b, off)[0]
    out = {}
    for i in range(n):
        tag, typ, cnt, val = struct.unpack_from("<HHII", b, off + 2 + 12 * i)
        size = TSIZE[typ] * cnt
        data = b[off + 2 + 12 * i + 8: off + 2 + 12 * i + 12][:size] if size <= 4 else b[val:val + size]
        if typ == 2:
            v = data.rstrip(b"\0").decode("latin1")
        elif typ in (5, 10):
            raw = struct.unpack("<%d%s" % (2 * cnt, "I" if typ == 5 else "i"), data)
            v = [raw[2 * k] / raw[2 * k + 1] for k in range(cnt)]
        else:
            v = list(struct.unpack("<%d%s" % (cnt, TFMT[typ]), data))
        out[TAGS.get(tag, tag)] = v
    return out


def _rational(x):
    d = 10000
    return int(round(x * d)), d


def write(path, entries):
    """entries: list of (name, type, values) with type 2 str, 3 short, 4 long, 10 srational, 11 float."""
    items = []
    for name, typ, v in entries:
        tag = NAMES[name] if isinstance(name, str) else name
        if typ == 2:
            data = v.encode("latin1") + b"\0"; cnt = len(data)
        elif typ == 10:
            v = list(np.ravel(v)); cnt = len(v)
            data = b"".join(struct.pack("<ii", *_rational(x)) for x in v)
        else:
            v = list(np.ravel(v)); cnt = len(v)
            data = struct.pack("<%d%s" % (cnt, TFMT[typ]), *v)
        items.append((tag, typ, cnt, data))
    items.sort()
    ifd_off = 8
    data_off = ifd_off + 2 + 12 * len(items) + 4
    head, blob = bytearray(), bytearray()
    for tag, typ, cnt, data in items:
        if len(data) <= 4:
            head += struct.pack("<HHI", tag, typ, cnt) + data + bytes(4 - len(data))
        else:
            if (data_off + len(blob)) % 2: blob += b"\0"
            head += struct.pack("<HHII", tag, typ, cnt, data_off + len(blob)); blob += data
    out = b"IIRC" + struct.pack("<I", ifd_off) + struct.pack("<H", len(items)) + bytes(head) + b"\0\0\0\0" + bytes(blob)
    open(path, "wb").write(out)


if __name__ == "__main__":
    if len(sys.argv) < 4 or sys.argv[1] != "--export-adobe":
        raise SystemExit("usage: dcp.py --export-adobe OUT.json DCP ...")
    out = {Path(f).name: {k: v for k, v in read(f).items() if k in ADOBE_FIELDS} for f in sys.argv[3:]}
    Path(sys.argv[2]).write_text(json.dumps(out, sort_keys=True))
    print(f"{sys.argv[2]}: {len(out)} profiles")
