# atomically

[![PyPI](https://img.shields.io/pypi/v/atomically.svg)](https://pypi.org/project/atomically/)
[![Tests](https://github.com/smizell/atomically-py/actions/workflows/test.yml/badge.svg)](https://github.com/smizell/atomically-py/actions/workflows/test.yml)
[![Changelog](https://img.shields.io/github/v/release/smizell/atomically?include_prereleases&label=changelog)](https://github.com/smizell/atomically-py/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/smizell/atomically-py/blob/main/LICENSE)

> [!NOTE]
> This library is for experimenting and prototyping at this point and may change considerably until it reaches version 1.0.0. Please be cautious about relying on this library at this point.

Write the smallest possible OpenAPI and generate the rest. Read more about this approach in the [Atomically repository](https://github.com/smizell/atomically-spec).

## Installation

You can use pipx to install this tool.

You can use `pipx` to install this tool.

* [Install pipx](https://pipx.pypa.io/latest/installation/)
* Run `pipx install atomically`

You can also use `pip`:

```bash
pip install atomically
```

## Usage

### As CLI

Run `atomically --help` to see all options.

To generate an OpenAPI from from an atomic file, run:

```sh
atomically generate path-to-atomic-file.yml
```

Read the [Atomically repository](https://github.com/smizell/atomically-spec) to see how to write atomic files. Check the `tests/atomic_files` directory in this repo to see examples.

### As Python library

```python
from atomically import Atomically

openapi = Atomically.from_file("atomically.yaml").generate()
with open("openapi.yaml", "w") as f:
    f.write(openapi.to_yaml())
```

## Development

To contribute to this library, first checkout the code. Then create a new virtual environment:

```bash
cd atomically
python -m venv venv
source venv/bin/activate
```

Now install the dependencies and test dependencies:

```bash
pip install -e '.[test]'
```

To run the tests:

```bash
pytest
```
