# metadata\_please

There are a couple of pretty decent ways to read metadata (`importlib-metadata`,
and `pkginfo`) but they tend to be pretty heavyweight.  This lib aims to do two
things, with as minimal dependencies as possible:

1. Support just enough metadata to be able to look up deps.
2. Do "the thing that pip does" when deciding what dist-info dir to look at.

# Usage

Example snippet to show how to get the metadata from a wheel. 

```python
from zipfile import ZipFile
from metadata_please import basic_metadata_from_wheel

zf = ZipFile('somepkg.whl')
print(basic_metadata_from_wheel(zf, "somepkg"))
```

### Output

```
BasicMetadata(
    reqs=[
        'build',
        'setuptools',
        'pip',
        'imperfect<1',
        'tomlkit<1',
        'click~=8.0',
        'GitPython~=3.1.18',
        'metatron==0.60.0',
        'pkginfo~=1.9',
        'pyyaml~=6.0',
        'runez~=5.2',
        'pathspec<1',
        'virtualenv<20.21',
        'tox~=3.28',
        'requests~=2.27',
        'urllib3~=1.26'
    ],
    provides_extra=frozenset(),
    name='pynt',
    requires_python='>=3.6',
    url='https://stash.corp.netflix.com/projects/NFPY/repos/pynt/browse',
    project_urls={}
)
```

The metadata can be extracted from a `wheel`, `sdist` (zip or tarball). Check [`__init__.py`](metadata_please/__init__.py) file for all available functions.

# Version Compat

Usage of this library should work back to 3.7, but development (and mypy
compatibility) only on 3.10-3.12.  Linting requires 3.12 for full fidelity.

# License

metadata\_please is copyright [Tim Hatch](https://timhatch.com/), and licensed under
the MIT license.  I am providing code in this repository to you under an open
source license.  This is my personal repository; the license you receive to
my code is from me and not from my employer. See the `LICENSE` file for details.
