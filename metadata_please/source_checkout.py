"""
Best-effort metadata extraction for "source checkouts" -- e.g. a local dir containing pyproject.toml.

This is different from an (extracted) sdist, which *should* have a generated dist-info already.

Prefers:
- PEP 621 metadata (pyproject.toml)
- Poetry metadata (pyproject.toml)
- Setuptools static metadata (setup.cfg)
- Setuptools, low effort reading (setup.py)

Notably, does not read nontrivial setup.py or attempt to emulate anything that can't be read staticly.
"""

import ast
import re
from dataclasses import asdict
from pathlib import Path

try:
    import tomllib as toml
except ImportError:
    import toml  # type: ignore[no-redef,unused-ignore]

from configparser import NoOptionError, NoSectionError, RawConfigParser

from packaging.utils import canonicalize_name

from .source_checkout_ast import SetupFindingVisitor, UNKNOWN

from .types import BasicMetadata

OPERATOR_RE = re.compile(r"([<>=~]+)(\d.*)")


def combine_markers(*markers: str) -> str:
    filtered_markers = [m for m in markers if m and m.strip()]
    if len(filtered_markers) == 0:
        return ""
    elif len(filtered_markers) == 1:
        return filtered_markers[0]
    else:
        return " and ".join(f"({m})" for m in filtered_markers)


def merge_extra_marker(extra_name: str, value: str) -> str:
    """Simulates what a dist-info requirement string would look like if also restricted to an extra."""
    if ";" not in value:
        return f'{value} ; extra == "{extra_name}"'
    else:
        a, _, b = value.partition(";")
        a = a.strip()
        b = b.strip()
        c = f'extra == "{extra_name}"'
        return f"{a} ; {combine_markers(b, c)}"


def from_source_checkout(path: Path) -> bytes:
    return (
        from_pep621_checkout(path)
        or from_poetry_checkout(path)
        or from_setup_cfg_checkout(path)
        or from_setup_py_checkout(path)
    )


def from_pep621_checkout(path: Path) -> bytes:
    """
    Returns a metadata snippet (which is zero-length if this is none of this style).
    """
    try:
        data = (path / "pyproject.toml").read_text()
    except FileNotFoundError:
        return b""
    doc = toml.loads(data)

    buf: list[str] = []
    for dep in doc.get("project", {}).get("dependencies", ()):
        buf.append(f"Requires-Dist: {dep}\n")
    for k, v in doc.get("project", {}).get("optional-dependencies", {}).items():
        extra_name = canonicalize_name(k)
        buf.append(f"Provides-Extra: {extra_name}\n")
        for i in v:
            buf.append("Requires-Dist: " + merge_extra_marker(extra_name, i) + "\n")

    name = doc.get("project", {}).get("name")
    if name:
        buf.append(f"Name: {name}\n")

    # Version
    version = doc.get("project", {}).get("version")
    if version:
        buf.append(f"Version: {version}\n")

    # Requires-Python
    requires_python = doc.get("project", {}).get("requires-python")
    if requires_python:
        buf.append(f"Requires-Python: {requires_python}\n")

    # Project-URL
    urls = doc.get("project", {}).get("urls")
    if urls:
        for k, v in urls.items():
            buf.append(f"Project-URL: {k}={v}\n")

    # Author
    authors = doc.get("project", {}).get("authors")
    if authors:
        for author in authors:
            try:
                buf.append(f"Author: {author.get('name')}\n")
            except AttributeError:
                pass
            try:
                buf.append(f"Author-Email: {author.get('email')}\n")
            except AttributeError:
                pass

    # Summary
    summary = doc.get("project", {}).get("description")
    if summary:
        buf.append(f"Summary: {summary}\n")

    # Description
    description = doc.get("project", {}).get("readme")
    if description:
        buf.append(f"Description: {description}\n")

    # Keywords
    keywords = doc.get("project", {}).get("keywords")
    if keywords:
        buf.append(f"Keywords: {keywords}\n")

    return "".join(buf).encode("utf-8")


def _translate_caret(specifier: str) -> str:
    """
    Given a string like "^0.2.3" returns ">=0.2.3,<0.3.0".
    """
    assert "," not in specifier
    parts = specifier[1:].split(".")
    while len(parts) < 3:
        parts.append("0")

    for i in range(len(parts)):
        if parts[i] != "0":
            # The docs are not super clear about how this behaves, but let's
            # assume integer-valued parts and just let the exception raise
            # otherwise.
            incremented = parts[:]
            incremented[i] = str(int(parts[i]) + 1)
            del incremented[i + 1 :]
            incremented_version = ".".join(incremented)
            break
    else:
        raise ValueError("All components were zero?")
    return f">={specifier[1:]},<{incremented_version}"


def _translate_tilde(specifier: str) -> str:
    """
    Given a string like "~1.2.3" returns ">=1.2.3,<1.3".
    """
    assert "," not in specifier
    parts = specifier[1:].split(".")
    incremented = parts[:2]
    incremented[-1] = str(int(incremented[-1]) + 1)
    incremented_version = ".".join(incremented)

    return f">={specifier[1:]},<{incremented_version}"


def from_poetry_checkout(path: Path) -> bytes:
    """
    Returns a metadata snippet (which is zero-length if this is none of this style).
    """
    try:
        data = (path / "pyproject.toml").read_text()
    except FileNotFoundError:
        return b""
    doc = toml.loads(data)

    saved_extra_constraints = {}

    buf: list[str] = []
    for k, v in doc.get("tool", {}).get("poetry", {}).get("dependencies", {}).items():
        if k == "python":
            pass  # TODO requires-python
        else:
            k = canonicalize_name(k)
            if isinstance(v, dict):
                version = v.get("version", "")
                if "extras" in v:
                    extras = "[%s]" % (",".join(v["extras"]))
                else:
                    extras = ""
                markers = v.get("markers", "")
                python = v.get("python", "")
                if python:
                    m = OPERATOR_RE.fullmatch(python)
                    assert m is not None
                    # TODO do ^/~ work on python version?
                    python = f"python_version {m.group(1)} '{m.group(2)}'"
                markers = combine_markers(markers, python)
                if markers:
                    markers = " ; " + markers
                optional = v.get("optional", False)
            else:
                version = v
                extras = ""
                markers = ""
                optional = False

            if not version:
                # e.g. git, path or url dependencies, skip for now
                continue

            # https://python-poetry.org/docs/dependency-specification/#version-constraints
            # 1.2.* type wildcards are supported natively in packaging
            if version.startswith("^"):
                version = _translate_caret(version)
            elif version.startswith("~"):
                version = _translate_tilde(version)
            elif version == "*":
                version = ""

            if version[:1].isdigit():
                version = "==" + version

            if optional:
                saved_extra_constraints[k] = (f"{extras}{version}", markers)
            else:
                buf.append(f"Requires-Dist: {k}{extras}{version}{markers}\n")

    for k, v in doc.get("tool", {}).get("poetry", {}).get("extras", {}).items():
        k = canonicalize_name(k)
        buf.append(f"Provides-Extra: {k}\n")
        for vi in v:
            vi = canonicalize_name(vi)
            constraints, markers = saved_extra_constraints[vi]
            buf.append(
                f"Requires-Dist: {vi}{constraints}{merge_extra_marker(k, markers)}"
            )

    name = doc.get("tool", {}).get("poetry", {}).get("name")
    if name:
        buf.append(f"Name: {name}\n")

    # Version
    version = doc.get("tool", {}).get("poetry", {}).get("version")
    if version:
        buf.append(f"Version: {version}\n")

    # Requires-Python
    requires_python = doc.get("tool", {}).get("poetry", {}).get("requires-python")
    if requires_python:
        buf.append(f"Requires-Python: {requires_python}\n")

    # Project-URL
    url = doc.get("tool", {}).get("poetry", {}).get("homepage")
    if url:
        buf.append(f"Home-Page: {url}\n")

    # Author
    authors = doc.get("tool", {}).get("poetry", {}).get("authors")
    if authors:
        buf.append(f"Author: {authors}\n")

    # Summary
    summary = doc.get("tool", {}).get("poetry", {}).get("description")
    if summary:
        buf.append(f"Summary: {summary}\n")

    # Description
    description = doc.get("tool", {}).get("poetry", {}).get("readme")
    if description:
        buf.append(f"Description: {description}\n")

    # Keywords
    keywords = doc.get("tool", {}).get("poetry", {}).get("keywords")
    if keywords:
        buf.append(f"Keywords: {keywords}\n")

    return "".join(buf).encode("utf-8")


def from_setup_cfg_checkout(path: Path) -> bytes:
    try:
        data = (path / "setup.cfg").read_text()
    except FileNotFoundError:
        return b""

    rc = RawConfigParser()
    rc.read_string(data)

    buf: list[str] = []
    try:
        buf.append(f"Name: {rc.get('metadata', 'name')}\n")
    except (NoOptionError, NoSectionError):
        pass

    # Requires-Python
    try:
        buf.append(f"Requires-Python: {rc.get('options', 'python_requires')}\n")
    except (NoOptionError, NoSectionError):
        pass

    # Home-Page
    try:
        buf.append(f"Home-Page: {rc.get('metadata', 'url')}\n")
    except (NoOptionError, NoSectionError):
        pass

    # Author
    try:
        buf.append(f"Author: {rc.get('metadata', 'author')}\n")
    except (NoOptionError, NoSectionError):
        pass

    # Author-Email
    try:
        buf.append(f"Author-Email: {rc.get('metadata', 'author_email')}\n")
    except (NoOptionError, NoSectionError):
        pass

    # Summary
    try:
        buf.append(f"Summary: {rc.get('metadata', 'description')}\n")
    except (NoOptionError, NoSectionError):
        pass

    # Description
    try:
        buf.append(f"Description: {rc.get('metadata', 'long_description')}\n")
    except (NoOptionError, NoSectionError):
        pass

    # Description-Content-Type
    try:
        buf.append(
            f"Description-Content-Type: {rc.get('metadata', 'long_description_content_type')}\n"
        )
    except (NoOptionError, NoSectionError):
        pass

    try:
        for dep in rc.get("options", "install_requires").splitlines():
            dep = dep.strip()
            if dep:
                buf.append(f"Requires-Dist: {dep}\n")
    except (NoOptionError, NoSectionError):
        pass

    try:
        section = rc["options.extras_require"]
    except KeyError:
        pass
    else:
        for k, v in section.items():
            extra_name = canonicalize_name(k)
            buf.append(f"Provides-Extra: {extra_name}\n")
            for i in v.splitlines():
                i = i.strip()
                if i:
                    buf.append(
                        "Requires-Dist: " + merge_extra_marker(extra_name, i) + "\n"
                    )

    return "".join(buf).encode("utf-8")


def from_setup_py_checkout(path: Path) -> bytes:
    try:
        data = (path / "setup.py").read_bytes()
    except FileNotFoundError:
        return b""

    v = SetupFindingVisitor()
    v.visit(ast.parse(data))

    if not v.setup_call_args:
        return b""

    buf = []

    r = v.setup_call_args.get("install_requires")
    if r:
        if r is UNKNOWN:
            raise ValueError("Complex setup call can't extract reqs")
        for dep in r:
            buf.append(f"Requires-Dist: {dep}\n")

    er = v.setup_call_args.get("extras_require")
    if er:
        if er is UNKNOWN:
            raise ValueError("Complex setup call can't extract extras")
        for k, deps in er.items():
            extra_name = canonicalize_name(k)
            buf.append(f"Provides-Extra: {extra_name}\n")
            for i in deps:
                buf.append("Requires-Dist: " + merge_extra_marker(extra_name, i) + "\n")

    n = v.setup_call_args.get("name")
    if n:
        if n is UNKNOWN:
            raise ValueError("Complex setup call can't extract name")
        buf.append(f"Name: {n}\n")

    n = v.setup_call_args.get("python_requires")
    if n:
        if n is UNKNOWN:
            raise ValueError("Complex setup call can't extract python_requires")
        buf.append(f"Requires-Python: {n}\n")

    n = v.setup_call_args.get("url")
    if n:
        if n is UNKNOWN:
            raise ValueError("Complex setup call can't extract url")
        buf.append(f"Home-Page: {n}\n")

    n = v.setup_call_args.get("project_urls")
    if n:
        if n is UNKNOWN:
            raise ValueError("Complex setup call can't extract project_urls")
        for k, v in n.items():
            buf.append(f"Project-URL: {k}={v}\n")

    return "".join(buf).encode("utf-8")


def basic_metadata_from_source_checkout(path: Path) -> BasicMetadata:
    return BasicMetadata.from_metadata(from_source_checkout(path))


if __name__ == "__main__":  # pragma: no cover
    import json
    import sys

    md = basic_metadata_from_source_checkout(Path(sys.argv[1]))
    if md.reqs or md.name:
        print(json.dumps(asdict(md), default=list))
    else:
        sys.exit(1)
