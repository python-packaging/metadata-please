from __future__ import annotations

from dataclasses import dataclass

from email import message_from_string
from typing import Sequence


@dataclass(frozen=True)
class BasicMetadata:
    # Popualted from Requires-Dist or requires.txt
    reqs: Sequence[str]
    # Populated from Provides-Extra
    provides_extra: set[str]

    @classmethod
    def from_metadata(cls, metadata: bytes) -> BasicMetadata:
        msg = message_from_string(metadata.decode("utf-8"))
        return BasicMetadata(
            msg.get_all("Requires-Dist") or (),
            set(msg.get_all("Provides-Extra") or ()),
        )

    @classmethod
    def from_sdist_pkg_info_and_requires(
        cls, pkg_info: bytes, requires: bytes
    ) -> BasicMetadata:
        # We can either get Provides-Extra from this, or from the section
        # headers in requires.txt...
        # msg = message_from_string(pkg_info.decode("utf-8"))
        return cls(
            *convert_sdist_requires(requires.decode("utf-8")),
        )


def convert_sdist_requires(data: str) -> tuple[list[str], set[str]]:
    # This is reverse engineered from looking at a couple examples, but there
    # does not appear to be a formal spec.  Mentioned at
    # https://setuptools.readthedocs.io/en/latest/formats.html#requires-txt
    # This snippet has existed in `honesty` for a couple of years now.
    current_markers = None
    extras: set[str] = set()
    lst: list[str] = []
    for line in data.splitlines():
        line = line.strip()
        if not line:
            continue
        elif line[:1] == "[" and line[-1:] == "]":
            current_markers = line[1:-1]
            if ":" in current_markers:
                # absl-py==0.9.0 and requests==2.22.0 are good examples of this
                extra, markers = current_markers.split(":", 1)
                if extra:
                    extras.add(extra)
                    current_markers = f"({markers}) and extra == {extra!r}"
                else:
                    current_markers = markers
            else:
                # this is an extras_require
                extras.add(current_markers)
                current_markers = f"extra == {current_markers!r}"
        else:
            if current_markers:
                lst.append(f"{line}; {current_markers}")
            else:
                lst.append(line)
    return lst, extras
