# Flameshow

[![tests](https://github.com/laixintao/flameshow/actions/workflows/pytest.yaml/badge.svg?branch=main)](https://github.com/laixintao/flameshow/actions/workflows/pytest.yaml)
[![codecov](https://codecov.io/gh/laixintao/flameshow/graph/badge.svg?token=XQCGN9GBL4)](https://codecov.io/gh/laixintao/flameshow)
[![PyPI](https://img.shields.io/pypi/v/flameshow.svg?logo=pypi&label=PyPI&logoColor=gold)](https://pypi.org/project/flameshow/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/flameshow?logo=python&logoColor=gold)
![PyPI - Downloads](https://img.shields.io/pypi/dm/flameshow)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Flameshow is a terminal Flamegraph viewer.

![](./docs/flameshow.gif)

## Features

- Renders Flamegraphs in your terminal
- Supports zooming in and displaying percentages
- Keyboard input is prioritized
- All operations can also be performed using the mouse.
- Can switch to different sample types

## Install

Flameshow is written in pure Python, so you can install via `pip`:

```shell
pip install flameshow
```

But you can also run it through [nix](https://nixos.org/):

```shell
nix run github:laixintao/flameshow
# Or if you want to install it imperatively:
nix profile install github:laixintao/flameshow
```

## Usage

View golang's goroutine dump:

```shell
$ curl http://localhost:9100/debug/pprof/goroutine -o goroutine.out
$ flameshow goroutine.out
```

After entering the TUI, the available actions are listed on Footer:

- <kbd>q</kbd> for quit
- <kbd>j</kbd> <kbd>i</kbd> <kbd>j</kbd> <kbd>k</kbd> or <kbd>←</kbd>
  <kbd>↓</kbd> <kbd>↑</kbd> <kbd>→</kbd> for moving around, and <kbd>Enter</kbd>
  for zoom in, then <kbd>Esc</kbd> for zoom out.
- You can also use a mouse, hover on a span will show it details, and click will
  zoom it.

## Supported Formats

As far as I know, there is no standard specification for profiles. Different
languages or tools might generate varying profile formats. I'm actively working
on supporting more formats. Admittedly, I might not be familiar with every tool
and its specific format. So, if you'd like Flameshow to integrate with a tool
you love, please feel free to reach out and submit an issue.

- Golang pprof
- [Brendan Gregg's Flamegraph](https://www.brendangregg.com/flamegraphs.html)

## Development

If you want to dive into the code and make some changes, start with:

```shell
git clone git@github.com:laixintao/flameshow.git
cd flameshow
pip install poetry
poetry install
```

---

This project is proudly powered by
[textual](https://github.com/Textualize/textual).
