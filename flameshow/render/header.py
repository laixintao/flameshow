import logging

from rich.text import Text
from textual import reactive
from textual.app import RenderResult
from textual.containers import Horizontal
from textual.css.query import NoMatches
from textual.reactive import Reactive, reactive
from textual.widget import Widget
from textual.widgets import Header


logger = logging.getLogger(__name__)


class HeaderIcon(Widget):
    """Display an 'icon' on the left of the header."""

    DEFAULT_CSS = """
    HeaderIcon {
        dock: left;
        padding-right: 1;
        width: 3;
        content-align: left middle;
    }
    """

    icon = reactive("🔥")
    """The character to use as the icon within the header."""

    def render(self) -> RenderResult:
        """Render the header icon.

        Returns:
            The rendered icon.
        """
        return self.icon


class HeaderTitle(Widget):
    """Display the title / subtitle in the header."""

    DEFAULT_CSS = """
    HeaderTitle {
        content-align: left middle;
        width: 20;
    }
    """

    text: Reactive[str] = Reactive("")
    """The main title text."""

    sub_text = Reactive("")
    """The sub-title text."""

    def render(self) -> RenderResult:
        """Render the title and sub-title.

        Returns:
            The value to render.
        """
        text = Text(self.text, no_wrap=True, overflow="ellipsis")
        if self.sub_text:
            text.append(" — ")
            text.append(self.sub_text, "dim")
        return text


class HeaderOpenedFilename(Widget):
    DEFAULT_CSS = """
    HeaderOpenedFilename {
        content-align: center middle;
        width: 70%;
    }
    """

    filename = reactive("")

    def __init__(self, filename, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filename = filename

    def render(self) -> RenderResult:
        text = Text(self.filename, no_wrap=True, overflow="ellipsis")
        logger.info("header filename: %s", self.filename)
        return text


class FlameshowHeader(Header):
    center_text = reactive("", init=False)

    def __init__(self, filename, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.center_text = filename

    def compose(self):
        yield HeaderIcon()
        yield Horizontal(
            HeaderTitle(),
            HeaderOpenedFilename(self.center_text, id="header-center-text"),
        )

    def watch_center_text(self, newtext):
        try:
            headero = self.query_one("#header-center-text")
        except NoMatches:
            pass
        else:
            headero.filename = newtext
