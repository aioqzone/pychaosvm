# ChaosVM Executor

A Python envirionment for Tencent ChaosVM.

## Usage

```python
from chaosvm import prepare
from urllib.parse import unquote

tdc = prepare(vmjs, "114.5.1.4")            # see docstring for more info
print( tdc.getInfo().__dict__ )             # a python dict
print( unquote(tdc.getData(None, True)) )   # a python str
```

To get `TDC_itoken`:

```python
# retrun the window object, instead of its TDC field
win = prepare(vmjs, "114.5.1.4", return_window=True)
tdc = win.TDC                               # the way to get TDC object
print( win.TDC_itoken )                     # 114514514:1919810810
```

## Install

This package is published on GitHub. It is indexed by [aioqzone-index][aioqzone-index].

```sh
pip install pychaosvm --index-url https://aioqzone.github.io/aioqzone-index/simple
```

## License

```
Copyright (C) 2023-2026 aioqzone

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```

- [AGPL 3.0 or later](./LICENSE)


[aioqzone-index]: https://aioqzone.github.io/aioqzone-index/ "aioqzone package index following PEP 503"
