"""Quick check: python -m ilda.test_reader [path.ild]"""
from __future__ import annotations

import struct
import sys
import tempfile
from pathlib import Path

from ilda.reader import read_ild_file


def _write_minimal_ild(path: Path, points: list[tuple[int, int, bool, int, int, int]]) -> None:
    header = bytearray(32)
    header[0:4] = b"ILDA"
    header[7] = 5
    header[8:16] = b"TEST    "
    header[16:24] = b"ILDFILE "
    struct.pack_into(">H", header, 24, len(points))
    struct.pack_into(">H", header, 26, 0)
    struct.pack_into(">H", header, 28, 1)
    body = bytearray()
    for i, (x, y, blank, r, g, b) in enumerate(points):
        status = 0
        if blank:
            status |= 0x40
        if i == len(points) - 1:
            status |= 0x80
        body.extend(struct.pack(">hh", x, y))
        body.append(status)
        body.extend(bytes([b & 0xFF, g & 0xFF, r & 0xFF]))
    eof = bytearray(32)
    eof[0:4] = b"ILDA"
    eof[7] = 5
    path.write_bytes(bytes(header) + bytes(body) + bytes(eof))


def main() -> None:
    if len(sys.argv) > 1:
        frames = read_ild_file(sys.argv[1])
    else:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "t.ild"
            _write_minimal_ild(
                p,
                [(0, 0, True, 0, 0, 0), (1000, 0, False, 0, 255, 0), (0, 0, False, 0, 255, 0)],
            )
            frames = read_ild_file(p)
    print(f"{len(frames)} frame(s), {len(frames[0].points)} points")


if __name__ == "__main__":
    main()
