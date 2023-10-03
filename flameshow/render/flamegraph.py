from collections import namedtuple
from rich.style import Style
from functools import lru_cache
import logging
import time
from typing import Dict, List

from rich.segment import Segment
from textual.binding import Binding
from textual.containers import Vertical
from textual.css.query import NoMatches
from textual.events import Resize
from textual.message import Message
from textual.reactive import reactive
from textual.strip import Strip
from textual.widget import Widget

from flameshow.models import Frame
from flameshow.utils import fgid
import iteround

from .span import Span
from .span_container import SpanContainer

logger = logging.getLogger(__name__)

FrameMap = namedtuple("FrameMap", "offset width followspaces")


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
        self.frame_maps = None

    def create_lines(self, profile):
        t1 = time.time()
        logger.info("start to create lines...")

        root = profile.root_stack

        lines = [
            [root],
        ]
        current = [root.children]
        line_no = 1

        while len(current) > 0:
            line = []
            next_line = []

            for children_group in current:
                for child in children_group:
                    line.append(child)
                    next_line.append(child.children)

            lines.append(line)
            line_no += 1
            current = next_line

        t2 = time.time()
        logger.info("create lines done, took %.2f seconds", t2 - t1)
        return lines

    def render_lines(self, crop):
        logger.info("render_lines!! crop: %s", crop)
        my_width = crop.size.width
        t1 = time.time()
        self.frame_maps = self.generate_frame_maps(my_width)
        t2 = time.time()
        logger.info("Generates frame maps, took %.4f seconds", t2 - t1)
        return super().render_lines(crop)

    @lru_cache
    def generate_frame_maps(self, width):
        """
        compute attributes for render for every frame

        only re-computes with width, focused_stack changeing
        """
        root = self.profile.root_stack
        st_count = len(root.values)
        frame_maps: Dict[int, List[FrameMap]] = {
            root._id: [FrameMap(0, width, 0) for _ in range(st_count)]
        }

        def _generate_for_children(frame):
            logger.debug("generate frame_maps for %s", frame)
            # generate for children
            my_maps = frame_maps[frame._id]
            for sample_i, my_map in enumerate(my_maps):
                parent_width = my_map.width
                if frame.values[sample_i] <= 0:
                    child_widthes = [0.0 for _ in frame.children]
                else:
                    child_widthes = [
                        child.values[sample_i]
                        / frame.values[sample_i]
                        * parent_width
                        for child in frame.children
                    ]

                # the tail_spaces here only for iteround, in the case that
                # child total is not 100% of parent, so tail need to be here
                # to take some spaces
                tail_spaces = float(parent_width - sum(child_widthes))
                if tail_spaces < 0:
                    logger.warning(
                        "Child total width is larger than parent: %f",
                        tail_spaces,
                    )
                    tail_spaces = 0.0
                else:
                    child_widthes.append(tail_spaces)

                rounded_child_widthes = iteround.saferound(
                    child_widthes, 0, topline=parent_width
                )

                offset = my_map.offset
                total_children = len(frame.children)
                for index, child in enumerate(frame.children):
                    child_width = int(rounded_child_widthes[index])
                    followspaces = 0
                    if index == total_children - 1:  # last one
                        if tail_spaces >= 0:
                            followspaces = int(tail_spaces)
                    frame_maps.setdefault(child._id, []).append(
                        FrameMap(
                            offset=offset,
                            width=child_width,
                            followspaces=followspaces,
                        )
                    )
                    offset += child_width

            for child in frame.children:
                _generate_for_children(child)

        _generate_for_children(root)

        return frame_maps

    def render_line(self, y: int) -> Strip:
        # logger.info("container_size: %s", self.container_size)
        line = self.lines[y]

        if not self.frame_maps:
            raise Exception("frame_maps is not init yet!")

        segments = []
        cursor = 0
        for frame in line:
            text = "▏" + frame.display_name
            frame_map = self.frame_maps[frame._id][self.sample_index]
            my_width = frame_map.width
            offset = frame_map.offset

            pre_pad = offset - cursor
            if pre_pad > 0:
                segments.append(Segment(" " * pre_pad))
                cursor += pre_pad
            elif pre_pad < 0:
                raise Exception("Prepad is negative! {}".format(pre_pad))

            if len(text) < my_width:
                text += " " * (my_width - len(text))
            if len(text) > my_width:
                text = text[:my_width]

            display_color = frame.display_color
            segments.append(
                Segment(
                    text,
                    Style(
                        color=display_color.get_contrast_text().rich_color,
                        bgcolor=display_color.rich_color,
                    ),
                )
            )
            cursor += my_width

            logger.debug(
                "%s in line %d, frame_map=%s",
                frame,
                y,
                frame_map,
            )

        strip = Strip(segments)
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
