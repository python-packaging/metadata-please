import unittest

from ..sdist import (
    basic_metadata_from_tar_sdist,
    basic_metadata_from_zip_sdist,
    from_tar_sdist,
    from_zip_sdist,
)
from ._tar import MemoryTarFile
from ._zip import MemoryZipFile
from .metadata_contents import METADATA_CONTENTS


class ZipSdistTest(unittest.TestCase):
    def test_requires_as_expected(self) -> None:
        z = MemoryZipFile(
            {
                "foo/__init__.py": b"",
                "foo.egg-info/PKG-INFO": b"\n",
                "foo.egg-info/requires.txt": b"""\
a
[e]
b
""",
            }
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
            {
                "foo/__init__.py": b"",
                "foo.egg-info/PKG-INFO": b"\n",
                "foo.egg-info/requires.txt": b"""\
a
[e]
b
""",
            }
        )
        bm = basic_metadata_from_zip_sdist(z)  # type: ignore
        self.assertEqual(
            ("a", "b; extra == 'e'"),
            bm.reqs,
        )
        self.assertEqual({"e"}, bm.provides_extra)

    def test_basic_metadata_no_requires_file(self) -> None:
        z = MemoryZipFile(
            {
                "foo/__init__.py": b"",
                "foo.egg-info/PKG-INFO": b"\n",
            },
        )
        bm = basic_metadata_from_zip_sdist(z)  # type: ignore
        self.assertEqual(
            (),
            bm.reqs,
        )
        self.assertEqual(set(), bm.provides_extra)

    def test_basic_metadata_absl_py_09(self) -> None:
        z = MemoryZipFile(
            {
                "foo/__init__.py": b"",
                "foo.egg-info/PKG-INFO": b"\n",
                "foo.egg-info/requires.txt": b"""\
six

[:python_version < "3.4"]
enum34
[test:python_version < "3.4"]
pytest
""",
            }
        )
        bm = basic_metadata_from_zip_sdist(z)  # type: ignore
        self.assertEqual(
            (
                "six",
                'enum34; python_version < "3.4"',
                # Quoting on the following line is an implementation detail
                "pytest; (python_version < \"3.4\") and extra == 'test'",
            ),
            bm.reqs,
        )
        self.assertEqual({"test"}, bm.provides_extra)

    def test_basic_metadata_fields(self) -> None:
        """
        Modern setuptools will drop a PKG-INFO file in a sdist that is very similar to the METADATA file in a wheel.
        """
        z = MemoryZipFile(
            {
                "foo/__init__.py": b"",
                "PKG-INFO": METADATA_CONTENTS,
            }
        )
        bm = basic_metadata_from_zip_sdist(z)  # type: ignore
        self.assertEqual(["foo"], bm.reqs)
        self.assertEqual("1.2.58", bm.version)
        self.assertEqual("Some Summary", bm.summary)
        self.assertEqual("http://example.com", bm.url)
        self.assertEqual("Chicken", bm.author)
        self.assertEqual("duck@example.com", bm.author_email)
        self.assertEqual("farm,animals", bm.keywords)
        self.assertEqual("text/markdown", bm.long_description_content_type)
        self.assertEqual("# Foo\n\nA very important package.\n", bm.description)


class TarSdistTest(unittest.TestCase):
    def test_requires_as_expected(self) -> None:
        t = MemoryTarFile(
            ["foo.egg-info/PKG-INFO", "foo.egg-info/requires.txt", "foo/__init__.py"],
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
            ["foo.egg-info/PKG-INFO", "foo.egg-info/requires.txt", "foo/__init__.py"],
            read_value=b"""\
a
[e]
b
""",
        )
        bm = basic_metadata_from_tar_sdist(t)  # type: ignore
        self.assertEqual(
            ("a", "b; extra == 'e'"),
            bm.reqs,
        )
        self.assertEqual({"e"}, bm.provides_extra)

    def test_metadata_fields_from_tar_sdist(self) -> None:
        t = MemoryTarFile(
            ["PKG-INFO", "foo/__init__.py"],
            read_value=METADATA_CONTENTS,
        )
        bm = basic_metadata_from_tar_sdist(t)  # type: ignore
        self.assertEqual("1.2.58", bm.version)
        self.assertEqual("Some Summary", bm.summary)
        self.assertEqual("http://example.com", bm.url)
        self.assertEqual("Chicken", bm.author)
        self.assertEqual("duck@example.com", bm.author_email)
        self.assertEqual("farm,animals", bm.keywords)
        self.assertEqual("text/markdown", bm.long_description_content_type)
        self.assertEqual("# Foo\n\nA very important package.\n", bm.description)
