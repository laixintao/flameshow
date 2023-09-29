# Flameshow

<a href="https://badge.fury.io/py/flameshow"><img src="https://badge.fury.io/py/flameshow.svg" alt="PyPI version"></a>

Flameshow is a terminal Flamegraph viewer.

![](./docs/flameshow.gif)
[![Test](https://github.com/laixintao/flameshow/actions/workflows/pytest.yaml/badge.svg)](https://github.com/laixintao/flameshow/actions/workflows/pytest.yaml)

## Features

- Renders Flamegraphs in your terminal
- Supports zooming in and displaying percentages
- Keyboard input is prioritized
- All operations can also be performed using the mouse.
- Can switch to different sample types

## Install

```shell
pip install flameshow
```

Requirements: needs `go` command available for building `.so` file for Golang.

(Python wheels are on the way!)

## Usage

View golang's goroutine dump:

```shell
$ curl http://localhost:9100/debug/pprof/goroutine -o goroutine.out
$ flameshow goroutine.out
```

use. Once you open Flameshow, the user-friendly UI should make it easy to
navigate.

Currently it only supports Golang's pprof dump, I am working on supporting more
formats

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
