import logging
import time

from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widget import Widget

from .span_container import SpanContainer

logger = logging.getLogger(__name__)


class FlameGraph(Widget):
    focused_stack_id = reactive(0)
    sample_index = reactive(0, init=False)

    def __init__(self, profile, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.profile = profile
        # +1 is extra "root" node
        self.viewer_height = self.profile.highest_lines + 1

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
