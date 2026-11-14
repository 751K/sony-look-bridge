#!/usr/bin/env python3
"""Build every release asset into OUT_DIR: the camera packs, the α7 V video LUT pack and SHA256SUMS.txt.

  1. build_packs.py SAMPLES_DIR OUT_DIR                 -> Sony-<camera>-Creative-Looks.zip
  2. video/video_look.py (α7 V sample) --write --eval  -> Sony-A7-V-SLog3-Video-LUTs/ (72 cubes)
     video/validate_luts.py, video/make_dctl.py, video/release_readme.txt
                                                        -> Sony-A7-V-SLog3-Video-LUTs.zip
  3. SHA256SUMS.txt over all ZIPs.
The LUTs depend only on the look parameters of the α7 V, not on which α7 V ARW is used.
Without Edit installed, set SONY_EDIT_TABLES (sonylook/edit_binary.py).
usage: make_release.py SAMPLES_DIR OUT_DIR --version vX.Y.Z [--jobs N]
"""
import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from build_packs import A7M5_SAMPLE, zip_pack  # noqa: E402

LUT_PACK = "Sony-A7-V-SLog3-Video-LUTs"


def run(*args):
    print("+", " ".join(str(a) for a in args), flush=True)
    subprocess.run([sys.executable, *map(str, args)], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("samples", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--version", required=True)
    ap.add_argument("--jobs", type=int)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    run(HERE / "build_packs.py", a.samples, a.out, *(["--jobs", a.jobs] if a.jobs else []))
    lut = a.out / LUT_PACK
    run(ROOT / "video/video_look.py", a.samples / A7M5_SAMPLE, "--write", "--eval", "--out", lut)
    run(ROOT / "video/validate_luts.py", lut)
    run(ROOT / "video/make_dctl.py", lut)
    readme = (ROOT / "video/release_readme.txt").read_text().replace("{version}", a.version)
    (lut / "README.txt").write_text(readme)
    zip_pack(lut)
    zips = sorted(a.out.glob("*.zip"))
    sums = "".join(f"{hashlib.sha256(z.read_bytes()).hexdigest()}  {z.name}\n" for z in zips)
    (a.out / "SHA256SUMS.txt").write_text(sums)
    print(f"{len(zips)} ZIPs -> {a.out}")


if __name__ == "__main__":
    main()
