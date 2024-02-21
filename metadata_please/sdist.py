from __future__ import annotations

from tarfile import TarFile
from zipfile import ZipFile

from .types import BasicMetadata, convert_sdist_requires


def from_zip_sdist(zf: ZipFile) -> bytes:
    """
    Returns an emulated dist-info metadata contents from the given ZipFile.
    """
    requires = [f for f in zf.namelist() if f.endswith("/requires.txt")]
    requires.sort(key=len)
    data = zf.read(requires[0])
    assert data is not None
    requires, extras = convert_sdist_requires(data.decode("utf-8"))

    buf: list[str] = []
    for req in requires:
        buf.append(f"Requires-Dist: {req}\n")
    for extra in sorted(extras):
        buf.append(f"Provides-Extra: {extra}\n")
    return ("".join(buf)).encode("utf-8")


def basic_metadata_from_zip_sdist(zf: ZipFile) -> BasicMetadata:
    requires = [f for f in zf.namelist() if f.endswith("/requires.txt")]
    requires.sort(key=len)
    data = zf.read(requires[0])
    assert data is not None
    return BasicMetadata.from_sdist_pkg_info_and_requires(b"", data)


def from_tar_sdist(tf: TarFile) -> bytes:
    """
    Returns an emulated dist-info metadata contents from the given TarFile.
    """
    # XXX Why do ZipFile and TarFile not have a common interface ?!
    requires = [f for f in tf.getnames() if f.endswith("/requires.txt")]
    requires.sort(key=len)

    fo = tf.extractfile(requires[0])
    assert fo is not None

    requires, extras = convert_sdist_requires(fo.read().decode("utf-8"))

    buf: list[str] = []
    for req in requires:
        buf.append(f"Requires-Dist: {req}\n")
    for extra in sorted(extras):
        buf.append(f"Provides-Extra: {extra}\n")
    return ("".join(buf)).encode("utf-8")


def basic_metadata_from_tar_sdist(tf: TarFile) -> BasicMetadata:
    # XXX Why do ZipFile and TarFile not have a common interface ?!
    requires = [f for f in tf.getnames() if f.endswith("/requires.txt")]
    requires.sort(key=len)

    fo = tf.extractfile(requires[0])
    assert fo is not None

    return BasicMetadata.from_sdist_pkg_info_and_requires(b"", fo.read())
