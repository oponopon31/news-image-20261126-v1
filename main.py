"""news-image-20261126 entry program.

Writes the rendered image for Thursday 26 November 2026 to the output
path the grader expects. Pure Python standard library, no network, no
randomness, no clock: every run copies the same bytes.

The image itself lives in this repository as entry.png (1024x1024,
under 1 MiB). This program only copies it and checks the copy.
"""

import hashlib
import os
import struct
import sys

# The grader runs `python3 -P -s`, and -P drops the script's own directory
# from sys.path, so pin it back in before anything else.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

IMAGE = "entry.png"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def repo_file(name):
    """A file sitting next to this program in the repository."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, name)


def destination():
    """Where the image goes: $MAKEFUN_OUTPUT_DIR, else /output, else here."""
    chosen = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if chosen:
        return os.path.join(chosen, IMAGE)
    if os.path.isdir("/output"):
        return os.path.join("/output", IMAGE)
    return repo_file(IMAGE)


def check_png(blob):
    """Confirm the bytes are a whole PNG and read its pixel size."""
    if blob[:8] != PNG_MAGIC:
        raise ValueError("entry asset is not a PNG file")
    width, height = struct.unpack(">II", blob[16:24])
    if width > 1024 or height > 1024:
        raise ValueError("image is larger than 1024x1024")
    if len(blob) > 1048576:
        raise ValueError("image is larger than 1 MiB")
    # A whole image: the IEND chunk must be the last 12 bytes, with the
    # right length (0), type (IEND) and CRC for an empty chunk.
    if blob[-12:] != struct.pack(">I", 0) + b"IEND" + b"\xae\x42\x60\x82":
        raise ValueError("image is truncated: no IEND chunk at the end")
    return width, height


def main():
    with open(repo_file(IMAGE), "rb") as handle:
        blob = handle.read()

    width, height = check_png(blob)
    fingerprint = hashlib.sha256(blob).hexdigest()

    target = destination()
    folder = os.path.dirname(target)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(target, "wb") as handle:
        handle.write(blob)

    with open(target, "rb") as handle:
        again = handle.read()
    if hashlib.sha256(again).hexdigest() != fingerprint:
        raise ValueError("written copy differs from the repository asset")

    print("wrote %s" % target)
    print("sha256 %s" % fingerprint)
    print("bytes %d" % len(blob))
    print("dimensions %dx%d" % (width, height))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
