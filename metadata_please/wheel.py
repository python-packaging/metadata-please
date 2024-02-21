# Reference https://github.com/pypa/pip/blob/main/src/pip/_internal/utils/wheel.py
# for what pip is able to load.

from zipfile import ZipFile

from packaging.utils import canonicalize_name

from .types import BasicMetadata


class InvalidWheel(Exception):
    pass


def _distinfo_dir(zf: ZipFile) -> str:
    """
    Returns the top-level .dist-info dir or raises.
    """
    subdirs = {p.split("/", 1)[0] for p in zf.namelist()}
    info_dirs = [s for s in subdirs if s.endswith(".dist-info")]

    if not info_dirs:
        raise InvalidWheel("Zero .dist-info dirs in wheel")
    elif len(info_dirs) > 1:
        raise InvalidWheel(
            f"{len(info_dirs)} .dist-info dirs where there should be just one: {sorted(info_dirs)}"
        )

    return info_dirs[0]


def from_wheel(zf: ZipFile, project_name: str) -> bytes:
    """
    Given a ZipFile, find the metadata file and return its contents.

    You can use a ZipFile to wrap any file-like object, including a `seekablehttpfile`.
    """

    info_dir = _distinfo_dir(zf)
    if not canonicalize_name(info_dir).startswith(canonicalize_name(project_name)):
        raise InvalidWheel(f"Mismatched {info_dir} for {project_name}")

    return zf.read(f"{info_dir}/METADATA")


def basic_metadata_from_wheel(zf: ZipFile, project_name: str) -> BasicMetadata:
    return BasicMetadata.from_metadata(from_wheel(zf, project_name))
