import unittest

from ..sdist import (
    basic_metadata_from_tar_sdist,
    basic_metadata_from_zip_sdist,
    from_tar_sdist,
    from_zip_sdist,
)
from ._tar import MemoryTarFile
from ._zip import MemoryZipFile


class ZipSdistTest(unittest.TestCase):
    def test_requires_as_expected(self) -> None:
        z = MemoryZipFile(
            ["foo.egg-info/requires.txt", "foo/__init__.py"],
            read_value=b"""\
a
[e]
b
""",
        )
        metadata = from_zip_sdist(z)  # type: ignore
        self.assertEqual(
            b"""\
Requires-Dist: a
Requires-Dist: b; extra == 'e'
Provides-Extra: e
""",
            metadata,
        )

    def test_basic_metadata(self) -> None:
        z = MemoryZipFile(
            ["foo.egg-info/requires.txt", "foo/__init__.py"],
            read_value=b"""\
a
[e]
b
""",
        )
        bm = basic_metadata_from_zip_sdist(z)  # type: ignore
        self.assertEqual(
            ["a", "b; extra == 'e'"],
            bm.reqs,
        )
        self.assertEqual({"e"}, bm.provides_extra)

    def test_basic_metadata_absl_py_09(self) -> None:
        z = MemoryZipFile(
            ["foo.egg-info/requires.txt", "foo/__init__.py"],
            read_value=b"""\
six

[:python_version < "3.4"]
enum34
[test:python_version < "3.4"]
pytest
""",
        )
        bm = basic_metadata_from_zip_sdist(z)  # type: ignore
        self.assertEqual(
            [
                "six",
                'enum34; python_version < "3.4"',
                # Quoting on the following line is an implementation detail
                "pytest; (python_version < \"3.4\") and extra == 'test'",
            ],
            bm.reqs,
        )
        self.assertEqual({"test"}, bm.provides_extra)


class TarSdistTest(unittest.TestCase):
    def test_requires_as_expected(self) -> None:
        t = MemoryTarFile(
            ["foo.egg-info/requires.txt", "foo/__init__.py"],
            read_value=b"""\
a
[e]
b
""",
        )
        metadata = from_tar_sdist(t)  # type: ignore
        self.assertEqual(
            b"""\
Requires-Dist: a
Requires-Dist: b; extra == 'e'
Provides-Extra: e
""",
            metadata,
        )

    def test_basic_metadata(self) -> None:
        t = MemoryTarFile(
            ["foo.egg-info/requires.txt", "foo/__init__.py"],
            read_value=b"""\
a
[e]
b
""",
        )
        bm = basic_metadata_from_tar_sdist(t)  # type: ignore
        self.assertEqual(
            ["a", "b; extra == 'e'"],
            bm.reqs,
        )
        self.assertEqual({"e"}, bm.provides_extra)
