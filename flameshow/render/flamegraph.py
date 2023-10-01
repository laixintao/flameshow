import logging
import time

from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widget import Widget

from .span import Span
from .span_container import SpanContainer

logger = logging.getLogger(__name__)


class FlameGraph(Widget, can_focus=True):
    BINDINGS = [
        Binding("j,down", "move_down", "Down", key_display="↓"),
        Binding("k,up", "move_up", "Up", key_display="↑"),
        Binding("l,right", "move_right", "Right", key_display="→"),
        Binding("h,left", "move_left", "Left", key_display="←"),
        Binding("enter", "zoom_in", "Zoom In"),
        Binding("escape", "zoom_out", "Zoom Out", show=False),
    ]

    focused_stack_id = reactive(0)
    sample_index = reactive(0, init=False)

    def __init__(
        self, profile, focused_stack_id, sample_index, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.profile = profile
        # +1 is extra "root" node
        self.focused_stack_id = focused_stack_id
        self.sample_index = sample_index

    def compose(self):
        yield self.get_flamegraph()

    def get_flamegraph(self):
        stack = self.profile.id_store[self.focused_stack_id]
        logger.info("render frame: %s", stack)
        parents = self._render_parents(stack)

        t1 = time.time()
        total_frame = self._get_frames_should_render(stack)

        # 15, 100 and 4 is magic number that I tuned
        # they fit the performance best while rendering enough information
        # 4 keeps every render < 1second
        max_level = round(15 - total_frame / 100)
        max_level = max(4, max_level)
        t2 = time.time()

        logger.debug(
            "compute spans that should render, took %.3f, total sample=%d,"
            " max_level=%d",
            t2 - t1,
            total_frame,
            max_level,
        )
        children = SpanContainer(
            stack,
            "100%",
            level=max_level,
            i=self.sample_index,
            sample_unit=self.sample_unit,
        )

        widgets = [*parents, children]
        v = Vertical(
            *widgets,
            id="flamegraph-container",
        )
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

    def _get_frames_should_render(self, frame) -> int:
        if frame.values[self.sample_index] == 0:
            return 0

        count = 1
        for c in frame.children:
            count += self._get_frames_should_render(c)

        return count

    @property
    def sample_unit(self):
        return self.profile.sample_types[self.sample_index].sample_unit

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
            logger.warning(
                "Can not find the old_container of #flamegraph-container"
            )
        else:
            old_container.remove()

        new_flame = self.get_flamegraph()
        await self.mount(new_flame)

        # reset view_info_stack after new flamegraph is mounted
        # self._set_new_viewinfostack(stack)

        self.focus()

    def action_zoom_in(self):
        logger.info("Zoom in!")
