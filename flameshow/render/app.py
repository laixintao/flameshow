from datetime import datetime
import logging
import time
from typing import ClassVar

import textual
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widgets import Footer, Static, RadioSet, RadioButton
from textual.events import Click

from flameshow.parser import Stack
from flameshow.render.header import FlameshowHeader
from flameshow.utils import fgid
from flameshow import __version__

from .span_container import SpanContainer
from .span import Span

logger = logging.getLogger(__name__)


class FlameGraphScroll(VerticalScroll, inherit_bindings=False):
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("b", "scroll_up", "Scroll Up", show=True, key_display="B"),
        Binding("f,space", "scroll_down", "Scroll Down", show=True, key_display="F"),
        Binding("home", "scroll_home", "Scroll Home", show=False),
        Binding("end", "scroll_end", "Scroll End", show=False),
        Binding("pageup", "page_up", "Page Up", show=False),
        Binding("pagedown", "page_down", "Page Down", show=False),
    ]


class FlameGraphApp(App):
    BINDINGS = [
        Binding("j,down", "move_down", "Down", key_display="↓"),
        Binding("k,up", "move_up", "Up", key_display="↑"),
        Binding("l,right", "move_right", "Right", key_display="→"),
        Binding("h,left", "move_left", "Left", key_display="←"),
        Binding("enter", "zoom_in", "Zoom In"),
        Binding("escape", "zoom_out", "Zoom Out", show=False),
        Binding("d", "toggle_dark", "Toggle dark mode", show=False),
        Binding(
            "s",
            "switch_sample_type",
            "Switch Sample Type",
            priority=True,
        ),
        Binding("ctrl+c,q", "quit", "Quit", show=True, key_display="Q"),
    ]

    DEFAULT_CSS = """
    #span-detail-container {
        height: 6;
    }

    #span-detail {
        width: 1fr;
        padding: 0 1;
        border: round $secondary;
        border-subtitle-align: left;
        background:   $boost;
    }

    #sample-type-radio {
        width: 20%;
    }

    """

    focused_stack_id = reactive(0)
    sample_index = reactive(0, init=False)

    def __init__(
        self,
        profile,
        max_level,
        _debug_exit_after_rednder=False,
        default_sample_index=0,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.profile = profile
        self.root_stack = profile.root_stack
        self._create_time = time.time()
        self._rendered_once = False

        self._max_level = max_level
        # +1 is extra "root" node
        self.viewer_height = self.profile.highest_lines + 1
        self._debug_exit_after_rednder = _debug_exit_after_rednder
        logger.info("App render level limit to %d", self._max_level)

        self.view_info_stack = self.root_stack
        self.parents_that_only_one_child = []

        self.filename = self.profile.filename

        self.sample_index = default_sample_index

    def on_mount(self):
        logger.info("mounted")
        self.title = "flameshow"
        self.sub_title = f"v{__version__}"

        self.set_stack_detail(self.root_stack)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""

        center_text = self._center_header_text(self.sample_index)
        yield FlameshowHeader(center_text)

        options = [
            RadioButton(f"{s.sample_type}, {s.sample_unit}")
            for s in self.profile.sample_types
        ]
        # TODO for heap default to inuse bytes
        options[self.sample_index].value = True
        radioset = RadioSet(*options, id="sample-type-radio")
        yield Horizontal(
            Static(
                id="span-detail",
            ),
            radioset,
            id="span-detail-container",
        )

        yield FlameGraphScroll(
            Vertical(id="flamegraph-container"),
            id="flamegraph-out-container",
        )

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

        datetime_str = created_at.strftime("Dumped at %Y %b %d(%A) %H:%M:%S")
        return Static(datetime_str)

    def post_display_hook(self):
        if self._rendered_once:
            return
        self._rendered_once = True
        rendered_time = time.time()
        render_cost = rendered_time - self._create_time
        logger.info("First render cost %.2f s", render_cost)
        if self._debug_exit_after_rednder:
            logger.warn("_debug_exit_after_rednder set to True, exit now")
            self.exit()

    def render_flamegraph(self, stack):
        parents = self._render_parents(stack)
        children = SpanContainer(
            stack,
            "100%",
            level=self._max_level,
            i=self.sample_index,
            sample_unit=self.sample_unit,
        )

        widgets = [*parents, children]
        v = Vertical(
            *widgets,
            id="flamegraph-container",
        )
        v.styles.height = self.viewer_height
        return v

    def _render_parents(self, stack):
        parents = []
        parent = stack.parent
        logger.debug("stack name: %s %d", stack.name, stack._id)

        parents_that_only_one_child = {}
        while parent:
            parents_that_only_one_child[parent._id] = stack
            parents.append(parent)
            stack = parent
            parent = parent.parent

        parent_widgets = []
        for s in reversed(parents):
            parent_widgets.append(
                Span(
                    s,
                    is_deepest_level=False,
                    sample_index=self.sample_index,
                    sample_unit=self.sample_unit,
                    classes="parent-of-focus",
                )
            )

        self.parents_that_only_one_child = parents_that_only_one_child

        return parent_widgets

    async def watch_sample_index(self, sample_index):
        logger.info("sample index changed to %d", sample_index)

        center_text = self._center_header_text(self.sample_index)
        header = self.query_one("FlameshowHeader")
        header.center_text = center_text

        stack = self.profile.id_store[self.focused_stack_id]
        await self._rerender(stack, sample_index)

    async def watch_focused_stack_id(
        self,
        focused_stack_id,
    ):
        logger.info(f"{focused_stack_id=} changed")
        new_focused_stack = self.profile.id_store[focused_stack_id]
        await self._rerender(new_focused_stack, self.sample_index)

    async def _rerender(self, stack, sample_index):
        if not stack:
            return
        logger.info("re-render the new focused_stack: %s", stack.name)

        try:
            old_container = self.query_one("#flamegraph-container")
        except NoMatches:
            logger.warning("Can not find the old_container of #flamegraph-container")
        else:
            old_container.remove()

        out_container = self.query_one("#flamegraph-out-container")
        new_flame = self.render_flamegraph(stack)
        await out_container.mount(new_flame)

        # reset view_info_stack after new flamegraph is mounted
        self._set_new_viewinfostack(stack)

        flamegraph_continer = self.query_one("#flamegraph-out-container")
        flamegraph_continer.focus()

    def __debug_dom(self, node, indent: int):
        for c in node.children:
            logger.debug("%s %s", indent * " ", c)
            self.__debug_dom(c, indent + 2)

    @on(Span.SpanSelected)
    def handle_span_select(self, message):
        logger.info("app message: %s", message)
        newid = message.stack_id

        self.focused_stack_id = newid

    @on(Click)
    def handle_switch_to_mouse(self):
        logger.debug("mouse click")

    @on(RadioSet.Changed)
    async def handle_radioset_changed(self, e):
        logger.info("event: %s", e)
        self.sample_index = e.index

    def _set_new_viewinfostack(self, new_view_info_stack: Stack):
        old_view_info_stack = self.view_info_stack

        # delete old first
        try:
            self.query_one(f"#{fgid(old_view_info_stack._id)}").remove_class(
                "view-info-span"
            )
        except NoMatches:
            logger.warning(
                "try to remove view-info-span class from span, but not found"
            )

        # set new one
        _add_id = f"#{fgid(new_view_info_stack._id)}"
        try:
            new_view = self.query_one(_add_id)
        except NoMatches:
            logger.critical(
                "Not found when try to add class view-info-span to a Span, id={}"
                .format(_add_id)
            )
            return
        else:
            logger.info("add class to %s", new_view)
            new_view.add_class("view-info-span")
            self.view_info_stack = new_view_info_stack
            new_view.scroll_visible()

        # set the viewstack info
        self.set_stack_detail(new_view_info_stack)

        logger.debug("view: %s", self.view_info_stack.name)

    def action_move_down(self):
        logger.debug("move down")
        children = self.view_info_stack.children

        if not children:
            logger.debug("no more children")
            return

        if self.view_info_stack._id in self.parents_that_only_one_child:
            new_view_info_stack = self.parents_that_only_one_child[
                self.view_info_stack._id
            ]
            self._set_new_viewinfostack(new_view_info_stack)
        else:
            # go to the biggest value
            new_view_info_stack = self._get_biggest_exist_child(children)
            if not new_view_info_stack:
                logger.warn("Got no children displayed!")
                return
            self._set_new_viewinfostack(new_view_info_stack)

    def _get_biggest_exist_child(self, stacks):
        ordered = sorted(
            stacks, key=lambda s: s.values[self.sample_index], reverse=True
        )
        for s in ordered:
            _id = f"#{fgid(s._id)}"
            try:
                found = self.query_one(_id)
                if found:
                    return s
            except textual.css.query.NoMatches:
                pass

    def action_move_up(self):
        logger.debug("move up")
        parent = self.view_info_stack.parent

        if not parent:
            logger.debug("no more children")
            return

        new_view_info_stack = parent
        self._set_new_viewinfostack(new_view_info_stack)

    def action_move_right(self):
        logger.debug("move right")

        right = self._find_right_sibling(self.view_info_stack)

        if not right:
            logger.debug("Got no right sibling")
            return

        self._set_new_viewinfostack(right)

    def action_move_left(self):
        logger.debug("move left")

        left = self._find_left_sibling(self.view_info_stack)

        if not left:
            logger.debug("Got no left sibling")
            return

        self._set_new_viewinfostack(left)

    def _find_left_sibling(self, me):
        """
        Find left.
        Even not currently dislayed, still can be viewed on detail.
        No need to check if the fgid is currently rendered.
        """
        my_parent = me.parent
        while my_parent:
            siblings = my_parent.children
            if len(siblings) >= 2:
                my_index = siblings.index(me)
                left_index = my_index - 1
                if left_index >= 0:
                    return siblings[left_index]

            me = my_parent
            my_parent = my_parent.parent

    def _find_right_sibling(self, me):
        my_parent = me.parent
        while my_parent:
            siblings = my_parent.children
            if len(siblings) >= 2:
                my_index = siblings.index(me)
                right_index = my_index + 1
                if right_index < len(siblings):
                    return siblings[right_index]

            me = my_parent
            my_parent = my_parent.parent

    def action_zoom_in(self):
        logger.info("Zoom in!")
        self.focused_stack_id = self.view_info_stack._id

    def action_zoom_out(self):
        logger.info("Zoom out!")
        self.focused_stack_id = self.root_stack._id

    def action_switch_sample_type(self):
        logger.info("Focus on radio type")
        sample_radio = self.query_one("#sample-type-radio")
        if sample_radio.has_focus:
            sample_radio.blur()
        else:
            sample_radio.focus()

    def set_stack_detail(self, stack):
        span_detail = self.query_one("#span-detail")
        span_detail.border_subtitle = stack.render_title()
        span_detail.update(stack.render_detail(self.sample_index, self.sample_unit))

    @property
    def sample_unit(self):
        return self.profile.sample_types[self.sample_index].sample_unit

    def is_span_exist(self, span_id):
        _id = f"#{fgid(span_id)}"
        try:
            self.query_one(_id)
            return True
        except NoMatches:
            return False
