from __future__ import annotations

from dataclasses import dataclass, field

from email import message_from_string
from types import MappingProxyType
from typing import Mapping, Optional, Sequence


@dataclass(frozen=True)
class BasicMetadata:
    # Popualted from Requires-Dist or requires.txt
    reqs: Sequence[str] = ()
    # Populated from Provides-Extra
    provides_extra: frozenset[str] = field(default_factory=frozenset)
    # Populated from Name
    name: Optional[str] = None
    version: Optional[str] = None
    requires_python: Optional[str] = None
    url: Optional[str] = None
    project_urls: Mapping[str, str] = field(
        default_factory=lambda: MappingProxyType({})
    )
    author: Optional[str] = None
    author_email: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[str] = None
    long_description_content_type: Optional[str] = None

    def __or__(self, other: BasicMetadata) -> BasicMetadata:
        """
        Fieldwise `or` -- if both copies are truthy, prefer `other`'s.
        """
        # N.b. this can't use asdict because it tries to copy, and
        # MappingProxyType isn't pickleable.
        my_args = self.__dict__.copy()
        truthy_other_args = {k: v for k, v in other.__dict__.items() if v}
        my_args.update(truthy_other_args)
        return BasicMetadata(**my_args)

    @classmethod
    def from_metadata(cls, metadata: bytes) -> BasicMetadata:
        msg = message_from_string(metadata.decode("utf-8"))
        return BasicMetadata(
            msg.get_all("Requires-Dist") or (),
            frozenset(msg.get_all("Provides-Extra") or ()),
            msg.get("Name"),
            msg.get("Version"),
            msg.get("Requires-Python"),
            msg.get("Home-Page"),
            {
                k: v
                for k, _, v in map(
                    (lambda line: line.partition("=")), msg.get_all("Project-URL") or ()
                )
            },
            msg.get("Author"),
            msg.get("Author-Email"),
            msg.get("Summary"),
            msg.get("Description") or msg.get_payload() or None,
            msg.get("Keywords"),
            msg.get("Description-Content-Type"),
        )

    @classmethod
    def from_sdist_pkg_info_and_requires(
        cls, pkg_info: bytes, requires: bytes
    ) -> BasicMetadata:
        # Both of these can theoretically include Provides-Extra; we keep the
        # pkg-info version if present.

        pkg_info_metadata = cls.from_metadata(pkg_info)
        seq_requires, provides_extra = convert_sdist_requires(requires.decode("utf-8"))
        sdist_metadata = cls(reqs=seq_requires, provides_extra=provides_extra)

        return sdist_metadata | pkg_info_metadata


def convert_sdist_requires(data: str) -> tuple[tuple[str, ...], frozenset[str]]:
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
    return tuple(lst), frozenset(extras)
