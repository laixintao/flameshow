import logging
from rich.segment import Segment

from textual.strip import Strip
from flameshow.models import Frame
from flameshow.utils import fgid
from textual.message import Message
import time

from textual.binding import Binding
from textual.containers import Vertical
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widget import Widget
from textual.events import Resize

from .span import Span
from .span_container import SpanContainer

logger = logging.getLogger(__name__)


def percent_of_parent(child: Frame):
    parent = child.parent
    values_p = []
    for i in range(len(child.values)):
        if parent.values[i] == 0:
            values_p.append(0)
            continue
        logger.debug(
            f"{child.values=} {parent.values=}, {parent.values_p=},"
            f" {parent.name=}"
        )
        v = child.values[i] / parent.values[i] * parent.values_p[i]
        values_p.append(v)
    return values_p


def add_array(arr1, arr2):
    return list(map(sum, zip(arr1, arr2)))


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
    view_frame = reactive(None, init=False)

    class ViewFrameChanged(Message):
        """View Frame changed"""

        def __init__(self, frame) -> None:
            super().__init__()
            self.frame = frame

        def __repr__(self) -> str:
            return f"ViewFrameChanged({self.frame=})"

    def __init__(
        self,
        profile,
        focused_stack_id,
        sample_index,
        view_frame,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.profile = profile
        # +1 is extra "root" node
        self.focused_stack_id = focused_stack_id
        self.sample_index = sample_index
        self.view_frame = view_frame

        # pre-render
        self.lines = self.create_lines(profile)

    def create_lines(self, profile):
        t1 = time.time()
        logger.info("start to create lines...")

        root = profile.root_stack
        value_count = len(root.values)

        root.values_p = [1] * value_count
        root.offset_p = [0] * value_count

        lines = [
            [root],
        ]
        current = [root.children]
        line_no = 1

        while len(current) > 0:
            line = []
            next_line = []

            for children_group in current:
                group_offset = [0] * value_count
                for child in children_group:
                    # TODO cmopute for all values here
                    values_p = percent_of_parent(child)
                    offset_p = add_array(child.parent.offset_p, group_offset)

                    child.values_p = values_p
                    child.offset_p = offset_p

                    group_offset = add_array(group_offset, values_p)

                    logger.debug(
                        "%d, line created, name=%s, offset=%.2f, value=%.2f",
                        line_no,
                        child.name,
                        offset_p,
                        values_p,
                    )
                    line.append(child)
                    next_line.append(child.children)

            lines.append(line)
            line_no += 1
            current = next_line

        t2 = time.time()
        logger.info("create lines done, took %.2f seconds", t2 - t1)
        return lines

    def render_line(self, y: int) -> Strip:
        line = self.lines[y]
        width = 100
        index = 0
        segments = []

        progress = 0
        for frame in line:
            my_offset = round(width * frame.offset_p[index])
            my_width = round(width * frame.values_p[index])

            pad = my_offset - progress
            if pad:
                segments.append(Segment(" " * pad))

            text = "|" + frame.name
            if len(text) < my_width:
                text += " " * (my_width - len(text))
            if len(text) > my_width:
                text = text[:my_width]

            segments.append(Segment(text))

            progress += pad + my_width

            logger.debug(
                "%s in line %d should pad %d, offset=%d, width=%d",
                frame.name,
                y,
                pad,
                my_offset,
                my_width,
            )

        strip = Strip(segments, 100)
        return strip

    def on_resize(self, resize_event: Resize):
        size = resize_event.size
        virtual_size = resize_event.virtual_size
        logger.info(
            "FlameGraph got Resize event, size=%s, virtual_size=%s",
            size,
            virtual_size,
        )

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

    # async def watch_focused_stack_id(
    #     self,
    #     focused_stack_id,
    # ):
    #     logger.info(f"{focused_stack_id=} changed")
    #     await self._rerender()

    # async def watch_sample_index(self, new_sample_index):
    #     logger.info("sample_index changed to %d", new_sample_index)
    #     await self._rerender()

    async def _rerender(self):
        stack = self.profile.id_store[self.focused_stack_id]
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

        # force set class add the view_frame class back
        self.post_message(self.ViewFrameChanged(stack))
        await self.watch_view_frame(stack, stack)

    def action_zoom_in(self):
        logger.info("Zoom in!")
        self.focused_stack_id = self.view_frame._id

    def action_zoom_out(self):
        logger.info("Zoom out!")
        self.focused_stack_id = self.profile.root_stack._id

    def action_move_down(self):
        logger.debug("move down")
        view_frame = self.view_frame
        view_frame_id = view_frame._id
        children = view_frame.children

        if not children:
            logger.debug("no more children")
            return

        if view_frame_id in self.parents_that_only_one_child:
            new_view_info_frame = self.parents_that_only_one_child[
                view_frame_id
            ]
            self.post_message(self.ViewFrameChanged(new_view_info_frame))
        else:
            # go to the biggest value
            new_view_info_frame = self._get_biggest_exist_child(children)
            if not new_view_info_frame:
                logger.warn("Got no children displayed!")
                return
            self.post_message(self.ViewFrameChanged(new_view_info_frame))

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
            except NoMatches:
                pass

    def action_move_up(self):
        logger.debug("move up")
        parent = self.view_frame.parent

        if not parent:
            logger.debug("no more children")
            return

        self.post_message(self.ViewFrameChanged(parent))

    def action_move_right(self):
        logger.debug("move right")

        right = self._find_right_sibling(self.view_frame)

        logger.debug("found right sibling: %s, %s", right, right.values)
        if not right:
            logger.debug("Got no right sibling")
            return

        self.post_message(self.ViewFrameChanged(right))

    def _find_right_sibling(self, me):
        my_parent = me.parent
        while my_parent:
            siblings = my_parent.children
            if len(siblings) >= 2:
                choose_index = siblings.index(me)
                while choose_index < len(siblings):
                    choose_index = choose_index + 1
                    if (
                        choose_index < len(siblings)
                        and siblings[choose_index].values[self.sample_index]
                        > 0
                    ):
                        return siblings[choose_index]

            me = my_parent
            my_parent = my_parent.parent

    def action_move_left(self):
        logger.debug("move left")

        left = self._find_left_sibling(self.view_frame)

        if not left:
            logger.debug("Got no left sibling")
            return

        self.post_message(self.ViewFrameChanged(left))

    def _find_left_sibling(self, me):
        """
        Find left.
        Even not currently displayed, still can be viewed on detail.
        No need to check if the fgid is currently rendered.
        """
        my_parent = me.parent
        while my_parent:
            siblings = my_parent.children
            if len(siblings) >= 2:
                choose_index = siblings.index(me)
                # move left, until:
                # got a sibling while value is not 0 (0 won't render)
                # and index >= 0
                while choose_index >= 0:
                    choose_index = choose_index - 1
                    if (
                        choose_index >= 0
                        and siblings[choose_index].values[self.sample_index]
                        > 0
                    ):
                        return siblings[choose_index]

            me = my_parent
            my_parent = my_parent.parent

    async def watch_view_frame(self, old, new):
        if old:  # default is None
            old_id = old._id
            # delete old first
            try:
                old_dom = self.query_one(f"#{fgid(old_id)}")
                logger.info("delete class from old span: %s", old_dom)
                old_dom.remove_class("view-info-span")
            except NoMatches:
                logger.warning(
                    "try to remove view-info-span class from span, but not"
                    " found"
                )

        # set new one
        new_id = new._id
        _add_id = f"#{fgid(new_id)}"
        try:
            new_view = self.query_one(_add_id)
        except NoMatches:
            logger.critical(
                "Not found when try to add class view-info-span to a Span,"
                " id={}".format(_add_id)
            )
            return
        else:
            logger.info("add class to %s", new_view)
            new_view.add_class("view-info-span")
            new_view.scroll_visible()
