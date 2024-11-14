import unittest

from ..wheel import basic_metadata_from_wheel, from_wheel, InvalidWheel
from ._zip import MemoryZipFile
from .metadata_contents import METADATA_CONTENTS


class WheelTest(unittest.TestCase):
    def test_well_behaved(self) -> None:
        z = MemoryZipFile(
            {
                "foo.dist-info/METADATA": b"MD",
                "foo/__init__.py": b"",
            }
        )
        self.assertEqual(b"MD", from_wheel(z, "foo"))  # type: ignore
        self.assertEqual(["foo.dist-info/METADATA"], z.files_read)

    def test_actually_empty(self) -> None:
        z = MemoryZipFile({})
        with self.assertRaisesRegex(InvalidWheel, "Zero .dist-info dirs in wheel"):
            from_wheel(z, "foo")  # type: ignore

    def test_no_dist_info(self) -> None:
        z = MemoryZipFile({"foo/__init__.py": b""})
        with self.assertRaisesRegex(InvalidWheel, "Zero .dist-info dirs in wheel"):
            from_wheel(z, "foo")  # type: ignore

    def test_too_many_dist_info(self) -> None:
        z = MemoryZipFile(
            {"foo.dist-info/METADATA": b"", "bar.dist-info/METADATA": b""}
        )
        with self.assertRaisesRegex(
            InvalidWheel,
            r"2 .dist-info dirs where there should be just one: \['bar.dist-info', 'foo.dist-info'\]",
        ):
            from_wheel(z, "foo")  # type: ignore

    def test_bad_project_name(self) -> None:
        z = MemoryZipFile(
            {
                "foo.dist-info/METADATA": b"",
                "foo/__init__.py": b"",
            }
        )
        with self.assertRaisesRegex(InvalidWheel, "Mismatched foo.dist-info for bar"):
            from_wheel(z, "bar")  # type: ignore

    def test_basic_metadata(self) -> None:
        z = MemoryZipFile(
            {
                "foo.dist-info/METADATA": b"Requires-Dist: foo\n",
                "foo/__init__.py": b"",
            }
        )
        bm = basic_metadata_from_wheel(z, "foo")  # type: ignore
        self.assertEqual(["foo"], bm.reqs)

    def test_basic_metadata_more_fields(self) -> None:
        z = MemoryZipFile(
            {
                "foo.dist-info/METADATA": METADATA_CONTENTS,
                "foo/__init__.py": b"",
            }
        )
        bm = basic_metadata_from_wheel(z, "foo")  # type: ignore
        self.assertEqual(["foo"], bm.reqs)
        self.assertEqual("1.2.58", bm.version)
        self.assertEqual("Some Summary", bm.summary)
        self.assertEqual("http://example.com", bm.url)
        self.assertEqual("Chicken", bm.author)
        self.assertEqual("duck@example.com", bm.author_email)
        self.assertEqual("farm,animals", bm.keywords)
        self.assertEqual("text/markdown", bm.long_description_content_type)
        self.assertEqual("# Foo\n\nA very important package.\n", bm.description)
