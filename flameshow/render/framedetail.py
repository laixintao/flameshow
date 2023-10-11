import logging

from textual.containers import Vertical
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from flameshow.models import Frame
from flameshow.utils import sizeof

logger = logging.getLogger(__name__)


class FrameStatThis(Widget):
    frame = reactive(None, init=False)
    sample_index = reactive(None, init=False)

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
        self.composed = False
        super().__init__(*args, **kwargs)

        self.profile = profile
        self.border_title = "This Instance"
        self.frame = frame
        self.sample_index = sample_index

    def compose(self):
        yield Static("Total", id="stat-this-total-label")
        yield Static("Self", id="stat-this-self-label")
        yield Static(
            self.frame_total_value_humanize, id="stat-this-total-value"
        )
        yield Static(self.frame_self_value_humanize, id="stat-this-self-value")
        yield Static(self.frame_total_percent, id="stat-this-total-percent")
        yield Static(self.frame_self_percent, id="stat-this-self-percent")
        self.composed = True

    def watch_frame(self, _: Frame):
        self._rerender()

    def watch_sample_index(self, _: int):
        self._rerender()

    def _rerender(self):
        if not self.composed:
            return
        logger.info(f"rerender --> {self.frame=} {self.sample_index=}")

        total_value_widget = self.query_one("#stat-this-total-value")
        total_value_widget.update(self.frame_total_value_humanize)

        total_percent_widget = self.query_one("#stat-this-total-percent")
        total_percent_widget.update(self.frame_total_percent)

        self_value_widget = self.query_one("#stat-this-self-value")
        self_value_widget.update(self.frame_self_value_humanize)

        self_percent_widget = self.query_one("#stat-this-self-percent")
        self_percent_widget.update(self.frame_self_percent)

    # TODO value should be rendered as different color based on total value
    @property
    def frame_total_value_humanize(self):
        value = self.frame.values[self.sample_index]
        value_display = self.humanize(self.sample_unit, value)
        return value_display

    @property
    def frame_self_value(self):
        value = self.frame.values[self.sample_index]
        self_value = value
        child_value = 0
        if self.frame.children:
            for child in self.frame.children:
                child_value += child.values[self.sample_index]

        self_value -= child_value
        return self_value

    @property
    def frame_self_value_humanize(self):
        value_display = self.humanize(self.sample_unit, self.frame_self_value)
        return value_display

    @property
    def frame_self_percent(self):
        frame = self.frame
        sample_index = self.sample_index

        if not frame.root.values[sample_index]:
            p_root = 0
        else:
            p_root = (
                self.frame_self_value / frame.root.values[sample_index] * 100
            )

        return f"{p_root:.2f}%"

    @property
    def frame_total_percent(self):
        frame = self.frame
        sample_index = self.sample_index

        if not frame.root.values[sample_index]:
            p_root = 0
        else:
            p_root = (
                frame.values[sample_index]
                / frame.root.values[sample_index]
                * 100
            )

        return f"{p_root:.2f}%"

    @property
    def sample_unit(self):
        return self.profile.sample_types[self.sample_index].sample_unit

    def humanize(self, sample_unit, value):
        display_value = value
        if sample_unit == "bytes":
            display_value = sizeof(value)

        return str(display_value)


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
    frame = reactive(None, init=False)
    sample_index = reactive(None, init=False)

    def __init__(self, frame, profile, sample_index, *args, **kwargs):
        self.composed = False
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
        self.composed = True

    def _rerender(self):
        if not self.composed:
            return
        try:
            span_detail = self.query_one("#span-detail")
        except NoMatches:
            return
        span_detail.border_title = self.frame.render_title()
        span_detail.update(
            self.frame.render_detail(self.sample_index, self.sample_unit)
        )

        try:
            frame_this_widget = self.query_one("FrameStatThis")
        except NoMatches:
            return

        frame_this_widget.frame = self.frame
        frame_this_widget.sample_index = self.sample_index

    @property
    def sample_unit(self):
        return self.profile.sample_types[self.sample_index].sample_unit

    def watch_frame(self, new_frame):
        logger.info("detailed frame changed to: %s", new_frame)
        self._rerender()

    def watch_sample_index(self, new_sample_index):
        logger.info("sample index changed to: %s", new_sample_index)
        self._rerender()
