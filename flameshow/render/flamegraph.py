from collections import namedtuple
from functools import lru_cache
import logging
import time
from typing import Dict, List

import iteround
from rich.segment import Segment
from rich.style import Style
from textual import on
from textual.binding import Binding
from textual.color import Color
from textual.events import Click, MouseMove, Resize, MouseEvent
from textual.message import Message
from textual.reactive import reactive
from textual.strip import Strip
from textual.widget import Widget

from flameshow.const import VIEW_INFO_COLOR


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

        def __init__(self, frame, by_mouse=False) -> None:
            super().__init__()
            self.frame = frame
            self.by_mouse = by_mouse

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
        self.frame_maps = None

        self.visible_start_y = 0

    def render_lines(self, crop):
        my_width = crop.size.width
        self.frame_maps = self.generate_frame_maps(
            my_width, self.focused_stack_id
        )

        logger.info("render crop: %s", crop)

        return super().render_lines(crop)

    @lru_cache
    def generate_frame_maps(self, width, focused_stack_id):
        """
        compute attributes for render for every frame

        only re-computes with width, focused_stack changing
        """
        t1 = time.time()
        logger.info(
            "lru cache miss, Generates frame map, for width=%d,"
            " focused_stack_id=%s",
            width,
            focused_stack_id,
        )
        frame_maps: Dict[int, List[FrameMap]] = {}
        current_focused_stack = self.profile.id_store[focused_stack_id]
        st_count = len(current_focused_stack.values)
        logger.debug("values count: %s", st_count)

        # set me to 100% and siblins to 0
        me = current_focused_stack
        while me:
            frame_maps[me._id] = [
                FrameMap(0, width, 0) for _ in range(st_count)
            ]
            me = me.parent

        logger.info("frame maps: %s", frame_maps)

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

        _generate_for_children(current_focused_stack)
        t2 = time.time()
        logger.info("Generates frame maps done, took %.4f seconds", t2 - t1)
        return frame_maps

    def render_line(self, y: int) -> Strip:
        # logger.info("container_size: %s", self.container_size)
        line = self.profile.lines[y]

        if not self.frame_maps:
            raise Exception("frame_maps is not init yet!")

        segments = []
        cursor = 0
        for frame in line:
            frame_maps = self.frame_maps.get(frame._id)
            if not frame_maps:
                logger.debug(
                    "frame %s not found in frame_map, not render this.", frame
                )
                continue
            frame_map = frame_maps[self.sample_index]
            my_width = frame_map.width
            if not my_width:
                continue

            text = "▏" + frame.display_name
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
            bold = False

            if frame is self.view_frame:
                display_color = Color.parse(VIEW_INFO_COLOR)
                bold = True

            if my_width > 0:
                # | is always default color
                segments.append(
                    Segment(
                        text[0],
                        Style(
                            bgcolor=display_color.rich_color,
                        ),
                    )
                )
            if my_width > 1:
                segments.append(
                    Segment(
                        text[1:],
                        Style(
                            color=display_color.get_contrast_text().rich_color,
                            bgcolor=display_color.rich_color,
                            bold=bold,
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

    @property
    def sample_unit(self):
        return self.profile.sample_types[self.sample_index].sample_unit

    def action_zoom_in(self):
        logger.info("Zoom in!")
        self.focused_stack_id = self.view_frame._id

    def action_zoom_out(self):
        logger.info("Zoom out!")
        self.focused_stack_id = self.profile.root_stack._id

    def action_move_down(self):
        logger.debug("move down")
        view_frame = self.view_frame
        children = view_frame.children

        if not children:
            logger.debug("no more children")
            return

        # go to the biggest value
        new_view_info_frame = self._get_biggest_exist_child(children)
        if not new_view_info_frame:
            logger.warn("Got no children displayed!")
            return
        self.post_message(self.ViewFrameChanged(new_view_info_frame))

    def _get_biggest_exist_child(self, stacks):
        biggest = max(stacks, key=lambda s: s.values[self.sample_index])
        return biggest

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

        logger.debug("found right sibling: %s", right)
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

    def on_mouse_move(self, event: MouseMove) -> None:
        hover_frame = self.get_frame_under_mouse(event)
        if hover_frame:
            logger.info("mouse hover on %s", hover_frame)
            self.post_message(self.ViewFrameChanged(hover_frame, by_mouse=True))

    @on(Click)
    def handle_click_frame(self, event: Click):
        frame = self.get_frame_under_mouse(event)
        self.focused_stack_id = frame._id

    def get_frame_under_mouse(self, event: MouseEvent):
        line_no = event.y + self.visible_start_y
        x = event.x

        if line_no >= len(self.profile.lines):
            return

        line = self.profile.lines[line_no]

        for frame in line:
            frame_maps = self.frame_maps.get(frame._id)
            if not frame_maps:
                # this frame not exist in current render
                continue
            frame_map = frame_maps[self.sample_index]
            offset = frame_map.offset
            width = frame_map.width

            if offset + width > x:  # find it!
                return frame
