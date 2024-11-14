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
        'cli-helpers[styles] >=2.2.1',
        'click >=4.1',
        'configobj >=5.0.5',
        'prompt-toolkit <4.0.0,>=3.0.3',
        'pygments >=1.6',
        'sqlparse >=0.4.4',
        "behave >=1.2.6 ; extra == 'dev'",
        "coverage >=7.2.7 ; extra == 'dev'",
        "pexpect >=4.9.0 ; extra == 'dev'",
        "pytest >=7.4.4 ; extra == 'dev'",
        "pytest-cov >=4.1.0 ; extra == 'dev'",
        "tox >=4.8.0 ; extra == 'dev'",
        "pdbpp >=0.10.3 ; extra == 'dev'"
    ],
    provides_extra=frozenset({'dev'}),
    name='litecli',
    version='1.12.4',
    requires_python='>=3.7',
    url=None,
    project_urls={'homepage, https://github.com/dbcli/litecli': ''},
    author=None,
    author_email='dbcli <litecli-users@googlegroups.com>',
    summary='CLI for SQLite Databases with auto-completion and syntax highlighting.',
    description='# litecli\n\n[![GitHub
Actions](https://github.com/dbcli/litecli/actions/workflows/ci.yml/badge.svg)](https://github.com/dbcli/litecli/actions/workflows/ci.yml "GitHub
Actions")\n\n[Docs](https://litecli.com)\n\nA command-line client for SQLite databases that has auto-completion and syntax
highlighting.\n\n![Completion](screenshots/litecli.png)\n![CompletionGif](screenshots/litecli.gif)\n\n## Installation\n\nIf you already know how to install python
packages, then you can install it via pip:\n\nYou might need sudo on linux.\n\n```\n$ pip install -U litecli\n```\n\nThe package is also available on Arch Linux through
AUR in two versions: [litecli](https://aur.archlinux.org/packages/litecli/) is based the latest release (git tag) and
[litecli-git](https://aur.archlinux.org/packages/litecli-git/) is based on the master branch of the git repo. You can install them manually or with an AUR helper such as
`yay`:\n\n```\n$ yay -S litecli\n```\n\nor\n\n```\n$ yay -S litecli-git\n```\n\nFor MacOS users, you can also use Homebrew to install it:\n\n```\n$ brew install
litecli\n```\n\n## Usage\n\n```\n$ litecli --help\n\nUsage: litecli [OPTIONS] [DATABASE]\n\nExamples:\n  - litecli sqlite_db_name\n```\n\nA config file is automatically
created at `~/.config/litecli/config` at first launch. For Windows machines a config file is created at `~\\AppData\\Local\\dbcli\\litecli\\config` at first launch. See
the file itself for a description of all available options.\n\n## Docs\n\nVisit: [litecli.com/features](https://litecli.com/features)\n',
    keywords=None,
    long_description_content_type='text/markdown'
)

```

The metadata can be extracted from a `wheel`, `sdist` (zip or tarball) or a source checkout (best effort). Check [`__init__.py`](metadata_please/__init__.py) file for all available functions.

# Version Compat

Usage of this library should work back to 3.7, but development (and mypy
compatibility) only on 3.10-3.12.  Linting requires 3.12 for full fidelity.

# License

metadata\_please is copyright [Tim Hatch](https://timhatch.com/), and licensed under
the MIT license.  I am providing code in this repository to you under an open
source license.  This is my personal repository; the license you receive to
my code is from me and not from my employer. See the `LICENSE` file for details.
