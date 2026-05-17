"""Read ILDA Image Data Transfer Format (Format 5, 2D true color)."""
from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

HEADER_SIZE = 32
POINT_SIZE = 8
FORMAT_5 = 5
ILDA_MAGIC = b"ILDA"


@dataclass(frozen=True)
class IldaPoint:
    x: int
    y: int
    blank: bool
    r: int
    g: int
    b: int


@dataclass(frozen=True)
class IldaFrameData:
    frame_name: str
    company_name: str
    frame_number: int
    total_frames: int
    points: list[IldaPoint]


def _read_ascii8(data: bytes, offset: int) -> str:
    return data[offset : offset + 8].decode("ascii", errors="replace").rstrip()


def _parse_header(data: bytes, offset: int) -> tuple[int, int, str, str, int, int, int]:
    if data[offset : offset + 4] != ILDA_MAGIC:
        raise ValueError(f"Not an ILDA header at offset {offset}")
    fmt = data[offset + 7]
    frame_name = _read_ascii8(data, offset + 8)
    company_name = _read_ascii8(data, offset + 16)
    record_count = struct.unpack_from(">H", data, offset + 24)[0]
    frame_number = struct.unpack_from(">H", data, offset + 26)[0]
    total_frames = struct.unpack_from(">H", data, offset + 28)[0]
    return fmt, record_count, frame_name, company_name, frame_number, total_frames, offset + HEADER_SIZE


def _parse_point(data: bytes, offset: int) -> IldaPoint:
    x, y = struct.unpack_from(">hh", data, offset)
    status = data[offset + 4]
    b = data[offset + 5]
    g = data[offset + 6]
    r = data[offset + 7]
    return IldaPoint(
        x=int(x),
        y=int(y),
        blank=bool(status & 0x40),
        r=int(r),
        g=int(g),
        b=int(b),
    )


def read_ild_file(path: Path | str) -> list[IldaFrameData]:
    """Parse all non-EOF frame sections from a .ild file."""
    raw = Path(path).read_bytes()
    if len(raw) < HEADER_SIZE:
        raise ValueError("File too small for ILDA header")

    frames: list[IldaFrameData] = []
    offset = 0
    while offset + HEADER_SIZE <= len(raw):
        fmt, record_count, frame_name, company_name, frame_number, total_frames, data_offset = (
            _parse_header(raw, offset)
        )
        if fmt != FORMAT_5:
            raise ValueError(f"Unsupported ILDA format {fmt} (only format 5 is supported)")
        if record_count == 0:
            break
        end = data_offset + record_count * POINT_SIZE
        if end > len(raw):
            raise ValueError("Truncated ILDA point data")
        points = [_parse_point(raw, data_offset + i * POINT_SIZE) for i in range(record_count)]
        frames.append(
            IldaFrameData(
                frame_name=frame_name,
                company_name=company_name,
                frame_number=frame_number,
                total_frames=total_frames,
                points=points,
            )
        )
        offset = end
    if not frames:
        raise ValueError("No ILDA frames found in file")
    return frames
