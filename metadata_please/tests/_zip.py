from __future__ import annotations

from typing import Sequence


class MemoryZipFile:
    def __init__(self, names: Sequence[str], read_value: bytes = b"foo") -> None:
        self.names = names
        self.read_value = read_value
        self.files_read: list[str] = []

    def namelist(self) -> Sequence[str]:
        return self.names[:]

    def read(self, filename: str) -> bytes:
        self.files_read.append(filename)
        return self.read_value
