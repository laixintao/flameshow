import logging
from textual.css.query import NoMatches

from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

logger = logging.getLogger(__name__)


class FrameStatCurrent(Widget):
    def render(self):
        return "asdf"


class FrameStack(Widget):
    def __init__(self, frame, profile, sample_index, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frame = frame
        self.sample_index = sample_index
        self.profile = profile

    def render(self):
        return self.frame.render_detail(self.sample_index, self.sample_unit)

    @property
    def sample_unit(self):
        return self.profile.sample_types[self.sample_index].sample_unit


class FrameDetail(Widget):
    DEFAULT_CSS = """
    FrameDetail {
        layout: horizontal;
        height: 10;
    }

    #span-detail {
        width: 1fr;
        height: 1fr;
        padding: 0 1;
        border: round $secondary;
        content-align-vertical: middle;
    }

    FrameStatCurrent {
        width: 10%;
        max-width: 20;
    }
    """
    frame = reactive(None)
    sample_index = reactive(None)

    def __init__(self, frame, profile, sample_index, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frame = frame
        self.sample_index = sample_index
        self.profile = profile

    def compose(self):
        yield FrameStatCurrent()
        yield Static(
            self.frame.render_detail(self.sample_index, self.sample_unit),
            id="span-detail",
        )

    def _rerender(self):
        try:
            span_detail = self.query_one("#span-detail")
        except NoMatches:
            return
        span_detail.border_title = self.frame.render_title()
        span_detail.update(
            self.frame.render_detail(self.sample_index, self.sample_unit)
        )

    @property
    def sample_unit(self):
        return self.profile.sample_types[self.sample_index].sample_unit

    def watch_frame(self, new_frame):
        logger.info("detailed frame changed to: %s", new_frame)
        self._rerender()

    def watch_sample_index(self, new_sample_index):
        logger.info("sample index changed to: %s", new_sample_index)
        self._rerender()
