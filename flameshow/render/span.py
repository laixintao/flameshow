import os
import logging

from rich.style import Style
from rich.text import Text
from textual import RenderableType
from textual.message import Message
from textual.widget import Widget

from flameshow.utils import fgid

logger = logging.getLogger(__name__)


class Span(Widget):
    DEFAULT_CSS = """
    Span {
        width: 100%;
        height: 1;
    }

    Span:hover {
        text-style: reverse bold;
    }
    Span.view-info-span {
        text-style: reverse bold;
    }

    Span.parent-of-focus {
        opacity: 50%;
    }
    """

    def __init__(
        self,
        s_stack,
        is_deepest_level,
        sample_index,
        sample_unit,
        *args,
        my_width=1,
        **kwargs,
    ):
        super().__init__(id=fgid(s_stack._id), *args, **kwargs)
        self.s_stack = s_stack
        self.s_deepest = is_deepest_level
        self.my_width = my_width
        self.i = sample_index
        self.sample_unit = sample_unit

    def on_mount(self) -> None:
        self.styles.background = self.s_stack.display_color
        self.styles.width = f"{self.my_width * 100:.2f}%"

        stack = self.s_stack
        self.tooltip = (
            stack.render_title()
            + os.linesep
            + stack.render_detail(self.i, self.sample_unit)
        )

    def render(self) -> RenderableType:
        # actuall, just display self.s_text will still work
        display_text = self.s_stack.display_name
        if self.s_deepest:
            display_text = "+more"
        display_color = self.s_stack.display_color
        t = Text.assemble(
            (
                "▏",
                Style(
                    bgcolor=display_color.rich_color,
                ),
            ),
            (
                # +200 to use text background cover original background
                display_text + " " * 200,
                Style(
                    color=display_color.get_contrast_text().rich_color,
                    bgcolor=display_color.rich_color,
                ),
            ),
        )

        return t

    class SpanSelected(Message):
        """Color selected message."""

        def __init__(self, stack_id) -> None:
            super().__init__()
            self.stack_id = stack_id

        def __repr__(self) -> str:
            return f"SpanSelected({self.stack_id=})"

    def on_mouse_up(self, e):
        e.stop()
        self.post_message(self.SpanSelected(self.s_stack._id))
