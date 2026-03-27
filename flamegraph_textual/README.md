# flamegraph-textual

Terminal flamegraph renderer built on Textual.

## Install

```shell
pip install flamegraph-textual
```

## Usage

```python
from textual.app import App, ComposeResult

from flamegraph_textual import FlameGraphView


class Demo(App):
    def compose(self) -> ComposeResult:
        profile_text = open("profile.out", "rb").read()
        yield FlameGraphView(profile_text, filename="profile.out")


Demo().run()
```
