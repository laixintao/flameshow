from datetime import datetime
import logging
from typing import ClassVar

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import VerticalScroll
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widgets import Footer, Static, Tabs, Tab

from flameshow import __version__
from flameshow.render.framedetail import FrameDetail, InformaionScreen
from flameshow.render.header import FlameshowHeader
from flameshow.render.tabs import SampleTabs

from .flamegraph import FlameGraph

logger = logging.getLogger(__name__)


class FlameGraphScroll(
    VerticalScroll, inherit_bindings=False, can_focus=False
):
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("b", "page_up", "Scroll Page Up", show=True, key_display="B"),
        Binding(
            "f,space",
            "page_down",
            "Scroll Page Down",
            show=True,
            key_display="F",
        ),
        Binding("home", "scroll_home", "Scroll Home", show=False),
        Binding("end", "scroll_end", "Scroll End", show=False),
        Binding("pageup", "page_up", "Page Up", show=False),
        Binding("pagedown", "page_down", "Page Down", show=False),
    ]

    def scroll_to_make_line_center(self, line_no):
        height = self.size.height
        start_line = max(0, line_no - round(height / 2))
        self.scroll_to(y=start_line)
        return start_line


class FlameshowApp(App):
    BINDINGS = [
        Binding("d", "toggle_dark", "Toggle dark mode", show=False),
        Binding(
            "tab,n",
            "switch_sample_type",
            "Switch Sample Type",
            priority=True,
            show=True,
            key_display="tab",
        ),
        Binding("ctrl+c,q", "quit", "Quit", show=True, key_display="Q"),
        Binding("o", "debug"),
        Binding("i", "information_screen", "Toggle view stack", show=True),
    ]

    DEFAULT_CSS = """
    #sample-type-radio {
        width: 20%;
        height: 1fr;
    }

    #profile-detail-info {
        text-align: right;
        color: grey;
    }

    Tabs {
        margin-bottom: 0;
    }
    """

    focused_stack_id = reactive(0)
    sample_index = reactive(None, init=False)
    view_frame = reactive(None, init=False)

    def __init__(
        self,
        profile,
        _debug_exit_after_rednder=False,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.profile = profile
        self.root_stack = profile.root_stack

        self._debug_exit_after_rednder = _debug_exit_after_rednder

        self.parents_that_only_one_child = []

        self.filename = self.profile.filename

        if profile.default_sample_type_index < 0:
            self.sample_index = (
                len(profile.sample_types) + profile.default_sample_type_index
            )
        else:
            self.sample_index = profile.default_sample_type_index

        fg = FlameGraph(
            self.profile,
            self.focused_stack_id,
            self.sample_index,
            self.root_stack,
        )
        fg.styles.height = self.profile.highest_lines + 1
        self.flamegraph_widget = fg

        tabs = [
            Tab(f"{s.sample_type}, {s.sample_unit}", id=f"sample-{index}")
            for index, s in enumerate(profile.sample_types)
        ]
        active_tab = tabs[self.sample_index].id
        self.tabs_widget = SampleTabs(*tabs, active=active_tab)

        self.frame_detail = FrameDetail(
            profile=profile,
            frame=self.root_stack,
            sample_index=self.sample_index,
        )
        self.show_information_screen = False

    def on_mount(self):
        logger.info("mounted")
        self.title = "flameshow"
        self.sub_title = f"v{__version__}"

        self.view_frame = self.root_stack

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""

        center_text = self._center_header_text(self.sample_index)
        yield FlameshowHeader(center_text)

        yield self.tabs_widget

        yield FlameGraphScroll(
            self.flamegraph_widget,
            id="flamegraph-out-container",
        )

        yield self.frame_detail

        yield self._profile_info(self.profile.created_at)
        yield Footer()

    def _center_header_text(self, sample_index):
        chosen_sample_type = self.profile.sample_types[sample_index]
        center_header = (
            f"{self.filename}: ({chosen_sample_type.sample_type},"
            f" {chosen_sample_type.sample_unit})"
        )
        return center_header

    def _profile_info(self, created_at: datetime):
        if not created_at:
            return Static("")

        datetime_str = created_at.astimezone().strftime(
            "Dumped at %Y %b %d(%A) %H:%M:%S %Z"
        )
        return Static(datetime_str, id="profile-detail-info")

    @on(FlameGraph.ViewFrameChanged)
    async def handle_view_frame_changed(self, e):
        logger.debug("app handle_view_frame_changed...")
        new_frame = e.frame
        by_mouse = e.by_mouse
        self.view_frame = new_frame

        self.flamegraph_widget.view_frame = new_frame

        if not by_mouse:
            frame_line_no = self.profile.frameid_to_lineno[new_frame._id]
            container = self.query_one("#flamegraph-out-container")
            container.scroll_to_make_line_center(line_no=frame_line_no)

    async def watch_sample_index(self, sample_index):
        logger.info("sample index changed to %d", sample_index)

        center_text = self._center_header_text(self.sample_index)
        try:
            header = self.query_one("FlameshowHeader")
        except NoMatches:
            logger.warning(
                "FlameshowHeader not found, might be not composed yet."
            )
            return
        header.center_text = center_text

        self.flamegraph_widget.sample_index = sample_index
        self.frame_detail.sample_index = sample_index

        if self.show_information_screen:
            information_screen = self.query_one("InformaionScreen")
            information_screen.sample_index = sample_index

    async def watch_view_frame(self, old, new_frame):
        logger.debug(
            "view info stack changed: old: %s, new: %s",
            old,
            new_frame,
        )
        self.frame_detail.frame = new_frame

    async def watch_focused_stack_id(
        self,
        focused_stack_id,
    ):
        logger.info(f"{focused_stack_id=} changed")
        self.flamegraph_widget.focused_stack_id = focused_stack_id

    def action_switch_sample_type(self):
        self.tabs_widget.action_next_tab()

    @property
    def sample_unit(self):
        return self.profile.sample_types[self.sample_index].sample_unit

    def action_debug(self):
        logger.info("currently focused on: %s", self.focused)

    @on(Tabs.TabActivated)
    def handle_sample_type_changed(self, event: Tabs.TabActivated):
        logger.info("Tab changed: %s", event)
        chosen_index = event.tab.id.split("-")[1]
        self.sample_index = int(chosen_index)

    def action_information_screen(self):
        if self.show_information_screen:
            self.pop_screen()
        else:
            self.push_screen(
                InformaionScreen(
                    self.view_frame,
                    self.sample_index,
                    self.sample_unit,
                    self.profile,
                )
            )
        self.show_information_screen = not self.show_information_screen

    @on(InformaionScreen.InformaionScreenPopped)
    def handle_inforamtion_screen_pop(self, event):
        logger.info("Information screen popped, event=%s", event)
        if self.show_information_screen:
            self.pop_screen()
        self.show_information_screen = False
