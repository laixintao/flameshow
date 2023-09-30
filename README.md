# Flameshow

<a href="https://badge.fury.io/py/flameshow"><img src="https://badge.fury.io/py/flameshow.svg" alt="PyPI version"></a>
[![tests](https://github.com/laixintao/flameshow/actions/workflows/pytest.yaml/badge.svg?branch=main)](https://github.com/laixintao/flameshow/actions/workflows/pytest.yaml)

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

At the moment, Flameshow supports only Golang's pprof dump. I'm actively working
on adding more formats. Admittedly, I might not be familiar with every tool and
its specifics. So, if you'd like Flameshow to integrate with a tool you love,
feel free reach out and drop an issue.

- Golang pprof

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
