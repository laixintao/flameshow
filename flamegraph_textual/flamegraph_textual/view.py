from __future__ import annotations

from typing import Union

from textual import on
from textual.binding import Binding
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Tab, Tabs

from flamegraph_textual.parsers import parse
from flamegraph_textual.render.app import FlameGraphScroll
from flamegraph_textual.render.framedetail import InformaionScreen
from flamegraph_textual.render.flamegraph import FlameGraph
from flamegraph_textual.render.framedetail import FrameDetail
from flamegraph_textual.render.tabs import SampleTabs


class FlameGraphView(Widget):
    """Embeddable flamegraph component that parses profile text."""

    BINDINGS = [
        Binding(
            "tab,n",
            "switch_sample_type",
            "Switch Sample Type",
            priority=True,
            show=True,
            key_display="tab",
        ),
        Binding("i", "information_screen", "Toggle view stack", show=True),
    ]

    focused_stack_id = reactive(0)
    sample_index = reactive(None, init=False)
    view_frame = reactive(None, init=False)

    def __init__(
        self,
        profile_text: Union[bytes, str],
        filename: str = "profile",
        sample_index: int | None = None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.profile = self._parse_profile(profile_text, filename)
        self.root_stack = self.profile.root_stack
        self.show_information_screen = False

        if sample_index is None:
            if self.profile.default_sample_type_index < 0:
                self.sample_index = (
                    len(self.profile.sample_types)
                    + self.profile.default_sample_type_index
                )
            else:
                self.sample_index = self.profile.default_sample_type_index
        else:
            self.sample_index = sample_index

        self.focused_stack_id = self.root_stack._id
        self.view_frame = self.root_stack

        self.flamegraph_widget = FlameGraph(
            self.profile,
            self.focused_stack_id,
            self.sample_index,
            self.root_stack,
        )
        self.flamegraph_widget.styles.height = (
            self.profile.highest_lines + 1
        )

        tabs = [
            Tab(
                f"{s.sample_type}, {s.sample_unit}",
                id=f"sample-{index}",
            )
            for index, s in enumerate(self.profile.sample_types)
        ]
        active_tab = tabs[self.sample_index].id
        self.tabs_widget = SampleTabs(*tabs, active=active_tab)

        self.frame_detail = FrameDetail(
            profile=self.profile,
            frame=self.root_stack,
            sample_index=self.sample_index,
        )

    def _parse_profile(
        self, profile_text: Union[bytes, str], filename: str
    ):
        if isinstance(profile_text, str):
            profile_bytes = profile_text.encode("utf-8")
        else:
            profile_bytes = profile_text
        return parse(profile_bytes, filename)

    def compose(self):
        yield self.tabs_widget
        yield FlameGraphScroll(
            self.flamegraph_widget,
            id="flamegraph-out-container",
        )
        yield self.frame_detail

    @on(FlameGraph.ViewFrameChanged)
    async def handle_view_frame_changed(self, e):
        new_frame = e.frame
        by_mouse = e.by_mouse
        self.view_frame = new_frame
        self.flamegraph_widget.view_frame = new_frame

        if not by_mouse:
            frame_line_no = self.profile.frameid_to_lineno[new_frame._id]
            container = self.query_one("#flamegraph-out-container")
            container.scroll_to_make_line_center(line_no=frame_line_no)

    async def watch_sample_index(self, sample_index):
        self.flamegraph_widget.sample_index = sample_index
        self.frame_detail.sample_index = sample_index

        if self.show_information_screen and self.app is not None:
            try:
                information_screen = self.app.query_one("InformaionScreen")
            except NoMatches:
                return
            information_screen.sample_index = sample_index

    async def watch_view_frame(self, old, new_frame):
        self.frame_detail.frame = new_frame

    async def watch_focused_stack_id(self, focused_stack_id):
        self.flamegraph_widget.focused_stack_id = focused_stack_id

    def action_switch_sample_type(self):
        self.tabs_widget.action_next_tab()

    @property
    def sample_unit(self):
        return self.profile.sample_types[self.sample_index].sample_unit

    @on(Tabs.TabActivated)
    def handle_sample_type_changed(self, event: Tabs.TabActivated):
        chosen_index = event.tab.id.split("-")[1]
        self.sample_index = int(chosen_index)

    def action_information_screen(self):
        if self.app is None:
            return
        if self.show_information_screen:
            self.app.pop_screen()
        else:
            self.app.push_screen(
                InformaionScreen(
                    self.view_frame,
                    self.sample_index,
                    self.sample_unit,
                    self.profile,
                )
            )
        self.show_information_screen = not self.show_information_screen
