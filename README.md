# metadata\_please

There are a couple of pretty decent ways to read metadata (`importlib-metadata`,
and `pkginfo`) but they tend to be pretty heavyweight.  This lib aims to do two
things, with as minimal dependencies as possible:

1. Support just enough metadata to be able to look up deps.
2. Do "the thing that pip does" when deciding what dist-info dir to look at.

# Version Compat

Usage of this library should work back to 3.7, but development (and mypy
compatibility) only on 3.10-3.12.  Linting requires 3.12 for full fidelity.

# License

metadata\_please is copyright [Tim Hatch](https://timhatch.com/), and licensed under
the MIT license.  I am providing code in this repository to you under an open
source license.  This is my personal repository; the license you receive to
my code is from me and not from my employer. See the `LICENSE` file for details.
