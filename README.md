# Flameshow

Flameshow is a terminal Flamegraph viewer.

![](./docs/flameshow.gif)

## Features

- Renders Flamegraphs in your terminal
- Supports zooming in and displaying percentages
- Keyboard input is prioritized
- However, all operations in Flameshow can also be performed using the mouse
- Can switch to different sample types

## Install

```shell
pip install flameshow
```

## Usage

View golang's goroutine dump:

```shell
$ curl http://localhost:9100/debug/pprof/goroutine -o goroutine.out
$ flameshow goroutine.out
```

Or using pipe:

```shell
curl http://localhost:9100/debug/pprof/goroutine | flameshow -
```

Once you open flameshow, you should be able to use it, the UI is very easy to
use.
