import logging
from textual.containers import Vertical
from textual.css.query import NoMatches

from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

logger = logging.getLogger(__name__)


class FrameStatThis(Widget):
    frame = reactive(None)
    sample_index = reactive(None)

    # width = 998.1MiB|998.1MiB
    DEFAULT_CSS = """
    FrameStatThis {
        height: 5;
        padding: 0 1;
        border: round $secondary;
        border-title-align: center;

        layout: grid;
        grid-size: 2 3;
        grid-rows: 1fr;
        grid-columns: 1fr;
        grid-gutter: 0 1;
    }

    #stat-this-total-label {
        background: $primary;
    }
    """

    def __init__(self, frame, profile, sample_index, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frame = frame
        self.sample_index = sample_index
        self.profile = profile
        self.border_title = "This Instance"

    def compose(self):
        yield Static("Total", id="stat-this-total-label")
        yield Static("Self", id="stat-this-self-label")
        yield Static("998.1MiB", id="stat-this-total-value")
        yield Static("0", id="stat-this-self-value")
        yield Static("1.0%", id="stat-this-total-percent")
        yield Static("0", id="stat-this-self-percent")

    @property
    def sample_unit(self):
        return self.profile.sample_types[self.sample_index].sample_unit


class FrameStatAll(Widget):
    frame = reactive(None)
    sample_index = reactive(None)

    # width = 998.1MiB|998.1MiB
    DEFAULT_CSS = """
    FrameStatAll {
        height: 5;
        padding: 0 1;
        border: round $secondary;
        border-title-align: center;

        layout: grid;
        grid-size: 2 3;
        grid-rows: 1fr;
        grid-columns: 1fr;
        grid-gutter: 0 1;
    }

    #stat-this-total-label {
        background: $primary;
    }
    """

    def __init__(self, frame, profile, sample_index, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frame = frame
        self.sample_index = sample_index
        self.profile = profile
        self.border_title = "All Instances"

    def compose(self):
        yield Static("Total", id="stat-all-total-label")
        yield Static("Self", id="stat-all-self-label")
        yield Static("998.1MiB", id="stat-all-total-value")
        yield Static("0", id="stat-all-self-value")
        yield Static("1.0%", id="stat-all-total-percent")
        yield Static("0", id="stat-all-self-percent")

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

    #stat-container {
        width: 20%;
        max-width: 25;
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
        yield Vertical(
            FrameStatThis(self.frame, self.profile, self.sample_index),
            FrameStatAll(self.frame, self.profile, self.sample_index),
            id="stat-container",
        )
        span_detail = Static(
            self.frame.render_detail(self.sample_index, self.sample_unit),
            id="span-detail",
        )
        span_detail.border_title = self.frame.render_title()
        yield span_detail

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