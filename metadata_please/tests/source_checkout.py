import tempfile

import unittest
from pathlib import Path

from ..source_checkout import basic_metadata_from_source_checkout
from ..types import BasicMetadata


class SourceCheckoutTest(unittest.TestCase):
    def test_pep621_empty(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            Path(d, "pyproject.toml").write_text("")
            self.assertEqual(
                BasicMetadata((), frozenset()),
                basic_metadata_from_source_checkout(Path(d)),
            )

    def test_pep621_extras(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            Path(d, "pyproject.toml").write_text(
                """\
[project]
dependencies = ["x", "y ; platform_system != 'Windows'"]

[project.optional-dependencies]
dev = ["Foo <= 2"]
marker = ["Bar ; python_version < '3'", "Baz <= 2; python_version < '3'"]
"""
            )
            rv = basic_metadata_from_source_checkout(Path(d))
            self.assertEqual(
                [
                    "x",
                    "y ; platform_system != 'Windows'",
                    'Foo <= 2 ; extra == "dev"',
                    "Bar ; (python_version < '3') and (extra == \"marker\")",
                    "Baz <= 2 ; (python_version < '3') and (extra == \"marker\")",
                ],
                rv.reqs,
            )
            self.assertEqual(frozenset({"dev", "marker"}), rv.provides_extra)

    def test_poetry_full(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            Path(d, "pyproject.toml").write_text(
                """\
[tool.poetry.dependencies]
python = "^3.6"
a = "1.0"
a2 = "*"
b = "^1.2.3"
b2 = "^0.2.3"
c = "~1.2.3"
c2 = "~1.2"
c3 = "~1"
d = {version="2", python="<3.11"}
e = {version="2", markers="sys_platform == 'darwin'"}
skipped = {git = "..."}
complex = {extras=["bar", "baz"], version="2"}
opt = { version = "^2.9", optional = true}
unused-extra = { version = "2", optional = true }

[tool.poetry.extras]
Foo = ["Opt"]  # intentionally uppercased
"""
            )
            rv = basic_metadata_from_source_checkout(Path(d))
            self.assertEqual(
                [
                    "a==1.0",
                    "a2",
                    "b>=1.2.3,<2",
                    "b2>=0.2.3,<0.3",
                    "c>=1.2.3,<1.3",
                    "c2>=1.2,<1.3",
                    "c3>=1,<2",
                    "d==2 ; python_version < '3.11'",
                    "e==2 ; sys_platform == 'darwin'",
                    "complex[bar,baz]==2",
                    'opt>=2.9,<3 ; extra == "foo"',
                ],
                rv.reqs,
            )
            self.assertEqual(
                frozenset({"foo"}),
                rv.provides_extra,
            )

    def test_setuptools_empty(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            Path(d, "setup.cfg").write_text("")
            self.assertEqual(
                BasicMetadata((), frozenset()),
                basic_metadata_from_source_checkout(Path(d)),
            )

    def test_setuptools_extras(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            Path(d, "setup.cfg").write_text(
                """\
[options]
install_requires =
    x
    y

[options.extras_require]
dev =
    # comment
    Foo <= 2
    # comment after
marker =
    Bar ; python_version < "3"
    Baz <= 2; python_version < "3"
"""
            )
            rv = basic_metadata_from_source_checkout(Path(d))
            self.assertEqual(
                [
                    "x",
                    "y",
                    'Foo <= 2 ; extra == "dev"',
                    'Bar ; (python_version < "3") and (extra == "marker")',
                    'Baz <= 2 ; (python_version < "3") and (extra == "marker")',
                ],
                rv.reqs,
            )
            self.assertEqual(
                frozenset({"dev", "marker"}),
                rv.provides_extra,
            )
