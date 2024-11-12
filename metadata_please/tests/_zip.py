from __future__ import annotations

from typing import Mapping, Sequence


class MemoryZipFile:
    def __init__(self, mock_files: Mapping[str, bytes] = {}) -> None:
        self.mock_files = mock_files
        self.files_read: list[str] = []

    def namelist(self) -> Sequence[str]:
        return list(self.mock_files.keys())

    def read(self, filename: str) -> bytes:
        self.files_read.append(filename)
        return self.mock_files[filename]
