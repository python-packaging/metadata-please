import unittest

from ..wheel import basic_metadata_from_wheel, from_wheel, InvalidWheel
from ._zip import MemoryZipFile


class WheelTest(unittest.TestCase):
    def test_well_behaved(self) -> None:
        z = MemoryZipFile(["foo.dist-info/METADATA", "foo/__init__.py"])
        self.assertEqual(b"foo", from_wheel(z, "foo"))  # type: ignore
        self.assertEqual(["foo.dist-info/METADATA"], z.files_read)

    def test_actually_empty(self) -> None:
        z = MemoryZipFile([])
        with self.assertRaisesRegex(InvalidWheel, "Zero .dist-info dirs in wheel"):
            from_wheel(z, "foo")  # type: ignore

    def test_no_dist_info(self) -> None:
        z = MemoryZipFile(["foo/__init__.py"])
        with self.assertRaisesRegex(InvalidWheel, "Zero .dist-info dirs in wheel"):
            from_wheel(z, "foo")  # type: ignore

    def test_too_many_dist_info(self) -> None:
        z = MemoryZipFile(["foo.dist-info/METADATA", "bar.dist-info/METADATA"])
        with self.assertRaisesRegex(
            InvalidWheel,
            r"2 .dist-info dirs where there should be just one: \['bar.dist-info', 'foo.dist-info'\]",
        ):
            from_wheel(z, "foo")  # type: ignore

    def test_bad_project_name(self) -> None:
        z = MemoryZipFile(["foo.dist-info/METADATA", "foo/__init__.py"])
        with self.assertRaisesRegex(InvalidWheel, "Mismatched foo.dist-info for bar"):
            from_wheel(z, "bar")  # type: ignore

    def test_basic_metadata(self) -> None:
        z = MemoryZipFile(
            ["foo.dist-info/METADATA", "foo/__init__.py"],
            read_value=b"Requires-Dist: foo\n",
        )
        bm = basic_metadata_from_wheel(z, "foo")  # type: ignore
        self.assertEqual(["foo"], bm.reqs)
