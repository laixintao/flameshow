__version__ = "0.1.0"

from flamegraph_textual.models import Frame, Profile, SampleType
from flamegraph_textual.parsers import parse
from flamegraph_textual.render.app import FlameGraphScroll, FlameshowApp
from flamegraph_textual.render.flamegraph import FlameGraph, FrameMap, add_array
from flamegraph_textual.view import FlameGraphView


class FlameGraphApp(FlameshowApp):
    """Convenience alias for embedding a full flamegraph app."""


__all__ = [
    "FlameGraph",
    "FlameGraphApp",
    "FlameGraphScroll",
    "FlameGraphView",
    "Frame",
    "FrameMap",
    "Profile",
    "SampleType",
    "add_array",
    "parse",
]
