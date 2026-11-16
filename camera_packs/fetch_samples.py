#!/usr/bin/env python3
"""Download the sample ARWs listed in samples.json and check their SHA-256.

Most samples are CC0 files from raw.pixls.us / rawdb.dnglab.org; the α7 V and α7C II samples are
assets of this repository's `samples` release.  Files already present with the right checksum are
kept.  usage: fetch_samples.py DIR
"""
import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

LIST = Path(__file__).resolve().parent / "samples.json"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fetch(url, path, tries=3):
    req = urllib.request.Request(url, headers={"User-Agent": "sony-look-bridge-ci"})
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
                while block := r.read(1 << 20):
                    f.write(block)
            return
        except OSError as e:
            if i == tries - 1:
                raise
            print(f"  retry after {e}", flush=True)
            time.sleep(5 * (i + 1))


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for e in json.loads(LIST.read_text()):
        path = out / e["file"]
        if path.exists() and sha256(path) == e["sha256"]:
            continue
        print(f"{e['file']} <- {e['source']}", flush=True)
        fetch(e["source"], path)
        if sha256(path) != e["sha256"]:
            path.unlink()
            raise SystemExit(f"{e['file']}: SHA-256 mismatch")
    print(f"{out}: samples ok")


if __name__ == "__main__":
    main()
