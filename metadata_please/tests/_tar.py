from __future__ import annotations

from io import BytesIO
from typing import Sequence


class MemoryTarFile:
    def __init__(self, names: Sequence[str], read_value: bytes = b"foo") -> None:
        self.names = names
        self.read_value = read_value
        self.files_read: list[str] = []

    def getnames(self) -> Sequence[str]:
        return self.names[:]

    def extractfile(self, filename: str) -> BytesIO:
        return BytesIO(self.read_value)
