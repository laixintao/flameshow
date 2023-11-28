from unittest.mock import MagicMock

import pytest
from textual.events import MouseMove

from flameshow.exceptions import RenderException
from flameshow.models import Frame
from flameshow.pprof_parser.parser import Profile, SampleType
from flameshow.render.flamegraph import FlameGraph, FrameMap, add_array

from ..utils import create_frame


def test_flamegraph_generate_frame_maps_parents_with_only_child():
    root = Frame("root", 0, values=[5])
    s1 = Frame("s1", 1, values=[4], parent=root)
    s2 = Frame("s2", 2, values=[2], parent=s1)

    root.children = [s1]
    s1.children = [s2]

    p = Profile(
        filename="abc",
        root_stack=root,
        highest_lines=1,
        total_sample=2,
        sample_types=[SampleType("goroutine", "count")],
        id_store={
            0: root,
            1: s1,
            2: s2,
        },
    )
    flamegraph_widget = FlameGraph(p, 0, -1, 0)

    # focus on 0 root
    frame_maps = flamegraph_widget.generate_frame_maps(20, 0)

    assert frame_maps == {
        0: [FrameMap(offset=0, width=20)],
        1: [FrameMap(offset=0, width=16)],
        2: [FrameMap(offset=0, width=8)],
    }


def test_add_array():
    assert add_array([1, 2, 3], [4, 5, 6]) == [5, 7, 9]


def test_flamegraph_generate_frame_maps():
    root = Frame("root", 0, values=[5])
    s1 = Frame("s1", 1, values=[4], parent=root)
    s2 = Frame("s2", 2, values=[1], parent=s1)
    s3 = Frame("s3", 3, values=[2], parent=s1)

    root.children = [s1]
    s1.children = [s2, s3]

    p = Profile(
        filename="abc",
        root_stack=root,
        highest_lines=1,
        total_sample=2,
        sample_types=[SampleType("goroutine", "count")],
        id_store={
            0: root,
            1: s1,
            2: s2,
            3: s3,
        },
    )
    flamegraph_widget = FlameGraph(p, 0, -1, 0)

    # focus on 0 root
    frame_maps = flamegraph_widget.generate_frame_maps(20, 1)

    assert frame_maps == {
        0: [FrameMap(offset=0, width=20)],
        1: [FrameMap(offset=0, width=20)],
        2: [FrameMap(offset=0, width=5)],
        3: [FrameMap(offset=5, width=10)],
    }

    # focus on 1
    frame_maps = flamegraph_widget.generate_frame_maps(20, 1)

    assert frame_maps == {
        0: [FrameMap(offset=0, width=20)],
        1: [FrameMap(offset=0, width=20)],
        2: [FrameMap(offset=0, width=5)],
        3: [FrameMap(offset=5, width=10)],
    }


def test_flamegraph_generate_frame_maps_child_width_0():
    root = Frame("root", 0, values=[5])
    s1 = Frame("s1", 1, values=[4], parent=root)
    s2 = Frame("s2", 2, values=[0], parent=s1)

    root.children = [s1]
    s1.children = [s2]

    p = Profile(
        filename="abc",
        root_stack=root,
        highest_lines=1,
        total_sample=2,
        sample_types=[SampleType("goroutine", "count")],
        id_store={
            0: root,
            1: s1,
            2: s2,
        },
    )
    flamegraph_widget = FlameGraph(p, 0, -1, 0)

    # focus on 0 root
    frame_maps = flamegraph_widget.generate_frame_maps(20, 1)

    assert frame_maps == {
        1: [FrameMap(offset=0, width=20)],
        0: [FrameMap(offset=0, width=20)],
        2: [FrameMap(offset=0, width=00)],
    }


def test_flamegraph_render_line():
    root = Frame("root", 0, values=[10])
    s1 = Frame("s1", 1, values=[4], parent=root)
    s2 = Frame("s2", 2, values=[3], parent=root)

    root.children = [s1, s2]

    p = Profile(
        filename="abc",
        root_stack=root,
        highest_lines=1,
        total_sample=2,
        sample_types=[SampleType("goroutine", "count")],
        id_store={
            0: root,
            1: s1,
            2: s2,
        },
    )
    flamegraph_widget = FlameGraph(p, 0, -1, root)
    flamegraph_widget.frame_maps = flamegraph_widget.generate_frame_maps(
        10, focused_stack_id=0
    )

    strip = flamegraph_widget.render_line(
        1,
    )

    line_strings = [seg.text for seg in strip._segments]

    assert line_strings == ["▏", "s1 ", "▏", "s2"]


def test_flamegraph_render_line_without_init():
    root = Frame("root", 0, values=[10])
    s1 = Frame("s1", 1, values=[4], parent=root)
    s2 = Frame("s2", 2, values=[3], parent=root)

    root.children = [s1, s2]

    p = Profile(
        filename="abc",
        root_stack=root,
        highest_lines=1,
        total_sample=2,
        sample_types=[SampleType("goroutine", "count")],
        id_store={
            0: root,
            1: s1,
            2: s2,
        },
    )
    flamegraph_widget = FlameGraph(p, 0, -1, 0)

    with pytest.raises(RenderException):
        flamegraph_widget.render_line(
            1,
        )


def test_flamegraph_action_zoom_in_zoom_out():
    root = Frame("root", 123, values=[5])
    s1 = Frame("s1", 42, values=[1])

    p = Profile(
        filename="abc",
        root_stack=root,
        highest_lines=1,
        total_sample=2,
        sample_types=[SampleType("goroutine", "count")],
        id_store={},
    )
    flamegraph_widget = FlameGraph(p, 0, -1, 0)
    flamegraph_widget.focused_stack_id = 333

    flamegraph_widget.action_zoom_out()

    assert flamegraph_widget.focused_stack_id == 123

    flamegraph_widget.view_frame = s1
    flamegraph_widget.action_zoom_in()
    assert flamegraph_widget.focused_stack_id == 42


def test_flamegraph_action_move_down():
    root = create_frame({
        "id": 0,
        "values": [10],
        "children": [
            {"id": 1, "values": [3], "children": []},
            {"id": 2, "values": [4], "children": []},
        ],
    })

    p = Profile(
        filename="abc",
        root_stack=root,
        highest_lines=10,
        total_sample=10,
        sample_types=[SampleType("goroutine", "count")],
        id_store={},
    )
    flamegraph_widget = FlameGraph(p, 0, -1, view_frame=root)
    flamegraph_widget.post_message = MagicMock()
    flamegraph_widget.action_move_down()

    flamegraph_widget.post_message.assert_called_once()
    args = flamegraph_widget.post_message.call_args[0]
    message = args[0]
    assert message.by_mouse == False
    assert message.frame._id == 2

    assert str(message) == "ViewFrameChanged(self.frame=<Frame #2 node-2>)"


def test_flamegraph_action_move_down_no_more_children():
    root = create_frame({
        "id": 0,
        "values": [10],
        "children": [],
    })

    p = Profile(
        filename="abc",
        root_stack=root,
        highest_lines=10,
        total_sample=10,
        sample_types=[SampleType("goroutine", "count")],
        id_store={},
    )
    flamegraph_widget = FlameGraph(p, 0, -1, view_frame=root)
    flamegraph_widget.post_message = MagicMock()
    flamegraph_widget.action_move_down()

    flamegraph_widget.post_message.assert_not_called()


def test_flamegraph_action_move_down_children_is_zero():
    root = create_frame({
        "id": 0,
        "values": [10],
        "children": [
            {"id": 1, "values": [0], "children": []},
        ],
    })

    p = Profile(
        filename="abc",
        root_stack=root,
        highest_lines=10,
        total_sample=10,
        sample_types=[SampleType("goroutine", "count")],
        id_store={},
    )
    flamegraph_widget = FlameGraph(p, 0, -1, view_frame=root)
    flamegraph_widget.post_message = MagicMock()
    flamegraph_widget.action_move_down()

    flamegraph_widget.post_message.assert_called_once()
    args = flamegraph_widget.post_message.call_args[0]
    message = args[0]
    assert message.by_mouse == False
    assert message.frame._id == 1


def test_flamegraph_action_move_up():
    id_store = {}
    root = create_frame(
        {
            "id": 0,
            "values": [10],
            "children": [
                {
                    "id": 1,
                    "values": [2],
                    "children": [
                        {"id": 3, "values": [1], "children": []},
                    ],
                },
                {"id": 2, "values": [3], "children": []},
            ],
        },
        id_store,
    )

    p = Profile(
        filename="abc",
        root_stack=root,
        highest_lines=10,
        total_sample=10,
        sample_types=[SampleType("goroutine", "count")],
        id_store=id_store,
    )
    flamegraph_widget = FlameGraph(p, 0, -1, view_frame=id_store[3])
    flamegraph_widget.post_message = MagicMock()
    flamegraph_widget.action_move_up()

    flamegraph_widget.post_message.assert_called_once()
    args = flamegraph_widget.post_message.call_args[0]
    message = args[0]
    assert message.by_mouse == False
    assert message.frame._id == 1

    # move up but no more parents
    flamegraph_widget.post_message = MagicMock()
    flamegraph_widget.view_frame = root
    flamegraph_widget.action_move_up()
    flamegraph_widget.post_message.assert_not_called()


def test_flamegraph_action_move_right_sibling_just_here():
    id_store = {}
    root = create_frame(
        {
            "id": 0,
            "values": [10],
            "children": [
                {
                    "id": 1,
                    "values": [2],
                    "children": [],
                },
                {"id": 2, "values": [3], "children": []},
            ],
        },
        id_store,
    )

    p = Profile(
        filename="abc",
        root_stack=root,
        highest_lines=10,
        total_sample=10,
        sample_types=[SampleType("goroutine", "count")],
        id_store=id_store,
    )
    flamegraph_widget = FlameGraph(p, 0, -1, view_frame=id_store[1])
    flamegraph_widget.post_message = MagicMock()
    flamegraph_widget.action_move_right()

    flamegraph_widget.post_message.assert_called_once()
    args = flamegraph_widget.post_message.call_args[0]
    message = args[0]
    assert message.by_mouse == False
    assert message.frame._id == 2

    # no more sibling
    flamegraph_widget = FlameGraph(p, 0, -1, view_frame=id_store[2])
    flamegraph_widget.post_message = MagicMock()
    flamegraph_widget.action_move_right()

    flamegraph_widget.post_message.assert_not_called()


def test_flamegraph_action_move_right_sibling_goes_to_parent():
    id_store = {}
    root = create_frame(
        {
            "id": 0,
            "values": [10],
            "children": [
                {
                    "id": 1,
                    "values": [2],
                    "children": [
                        {"id": 3, "values": [1], "children": []},
                    ],
                },
                {"id": 2, "values": [3], "children": []},
            ],
        },
        id_store,
    )

    p = Profile(
        filename="abc",
        root_stack=root,
        highest_lines=10,
        total_sample=10,
        sample_types=[SampleType("goroutine", "count")],
        id_store=id_store,
    )
    flamegraph_widget = FlameGraph(p, 0, -1, view_frame=id_store[3])
    flamegraph_widget.post_message = MagicMock()
    flamegraph_widget.action_move_right()

    flamegraph_widget.post_message.assert_called_once()
    args = flamegraph_widget.post_message.call_args[0]
    message = args[0]
    assert message.by_mouse == False
    assert message.frame._id == 2


def test_flamegraph_action_move_right_on_root():
    id_store = {}
    root = create_frame(
        {
            "id": 0,
            "values": [10],
            "children": [
                {
                    "id": 1,
                    "values": [2],
                    "children": [
                        {"id": 3, "values": [1], "children": []},
                    ],
                },
                {"id": 2, "values": [3], "children": []},
            ],
        },
        id_store,
    )

    p = Profile(
        filename="abc",
        root_stack=root,
        highest_lines=10,
        total_sample=10,
        sample_types=[SampleType("goroutine", "count")],
        id_store=id_store,
    )
    flamegraph_widget = FlameGraph(p, 0, -1, view_frame=id_store[0])
    flamegraph_widget.post_message = MagicMock()
    flamegraph_widget.action_move_right()

    flamegraph_widget.post_message.assert_not_called()


def test_flamegraph_action_move_left_sibling_just_here():
    id_store = {}
    root = create_frame(
        {
            "id": 0,
            "values": [10],
            "children": [
                {"id": 2, "values": [3], "children": []},
                {
                    "id": 1,
                    "values": [2],
                    "children": [],
                },
            ],
        },
        id_store,
    )

    p = Profile(
        filename="abc",
        root_stack=root,
        highest_lines=10,
        total_sample=10,
        sample_types=[SampleType("goroutine", "count")],
        id_store=id_store,
    )
    flamegraph_widget = FlameGraph(p, 0, -1, view_frame=id_store[1])
    flamegraph_widget.post_message = MagicMock()
    flamegraph_widget.action_move_left()

    flamegraph_widget.post_message.assert_called_once()
    args = flamegraph_widget.post_message.call_args[0]
    message = args[0]
    assert message.by_mouse == False
    assert message.frame._id == 2

    # no more sibling
    flamegraph_widget = FlameGraph(p, 0, -1, view_frame=id_store[2])
    flamegraph_widget.post_message = MagicMock()
    flamegraph_widget.action_move_left()

    flamegraph_widget.post_message.assert_not_called()


def test_flamegraph_action_move_left_sibling_goes_to_parent():
    id_store = {}
    root = create_frame(
        {
            "id": 0,
            "values": [10],
            "children": [
                {"id": 2, "values": [3], "children": []},
                {
                    "id": 1,
                    "values": [2],
                    "children": [
                        {"id": 3, "values": [1], "children": []},
                    ],
                },
            ],
        },
        id_store,
    )

    p = Profile(
        filename="abc",
        root_stack=root,
        highest_lines=10,
        total_sample=10,
        sample_types=[SampleType("goroutine", "count")],
        id_store=id_store,
    )
    flamegraph_widget = FlameGraph(p, 0, -1, view_frame=id_store[3])
    flamegraph_widget.post_message = MagicMock()
    flamegraph_widget.action_move_left()

    flamegraph_widget.post_message.assert_called_once()
    args = flamegraph_widget.post_message.call_args[0]
    message = args[0]
    assert message.by_mouse == False
    assert message.frame._id == 2


def test_flamegraph_action_move_left_on_root():
    id_store = {}
    root = create_frame(
        {
            "id": 0,
            "values": [10],
            "children": [
                {
                    "id": 1,
                    "values": [2],
                    "children": [
                        {"id": 3, "values": [1], "children": []},
                    ],
                },
                {"id": 2, "values": [3], "children": []},
            ],
        },
        id_store,
    )

    p = Profile(
        filename="abc",
        root_stack=root,
        highest_lines=10,
        total_sample=10,
        sample_types=[SampleType("goroutine", "count")],
        id_store=id_store,
    )
    flamegraph_widget = FlameGraph(p, 0, -1, view_frame=id_store[0])
    flamegraph_widget.post_message = MagicMock()
    flamegraph_widget.action_move_left()

    flamegraph_widget.post_message.assert_not_called()


def test_flamegraph_render_on_mouse_move():
    id_store = {}
    # 10
    # 3, 2
    #  , 1
    root = create_frame(
        {
            "id": 0,
            "values": [10],
            "children": [
                {"id": 2, "values": [3], "children": []},
                {
                    "id": 1,
                    "values": [2],
                    "children": [
                        {"id": 3, "values": [1], "children": []},
                    ],
                },
            ],
        },
        id_store,
    )

    p = Profile(
        filename="abc",
        root_stack=root,
        highest_lines=10,
        total_sample=10,
        sample_types=[SampleType("goroutine", "count")],
        id_store=id_store,
    )
    flamegraph_widget = FlameGraph(p, 0, -1, view_frame=id_store[3])
    flamegraph_widget.frame_maps = flamegraph_widget.generate_frame_maps(10, 0)
    flamegraph_widget.post_message = MagicMock()

    mouse_event = MouseMove(
        x=2,
        y=1,
        delta_x=0,
        delta_y=0,
        button=False,
        shift=False,
        meta=False,
        ctrl=False,
    )
    flamegraph_widget.on_mouse_move(mouse_event)

    flamegraph_widget.post_message.assert_called_once()
    args = flamegraph_widget.post_message.call_args[0]
    message = args[0]
    assert message.by_mouse == True
    assert message.frame._id == 2

    assert flamegraph_widget.focused_stack_id == 0
    flamegraph_widget.handle_click_frame(mouse_event)
    assert flamegraph_widget.focused_stack_id == 2

    # move to lines that empty
    flamegraph_widget.post_message = MagicMock()
    flamegraph_widget.on_mouse_move(
        MouseMove(
            x=1,
            y=2,
            delta_x=0,
            delta_y=0,
            button=False,
            shift=False,
            meta=False,
            ctrl=False,
        )
    )
    args = flamegraph_widget.post_message.assert_not_called()

    # just to move the the exact offset, should still work
    # should be hover on next span instead of last
    flamegraph_widget.post_message = MagicMock()
    flamegraph_widget.on_mouse_move(
        MouseMove(
            x=3,
            y=1,
            delta_x=0,
            delta_y=0,
            button=False,
            shift=False,
            meta=False,
            ctrl=False,
        )
    )
    flamegraph_widget.post_message.assert_called_once()
    args = flamegraph_widget.post_message.call_args[0]
    message = args[0]
    assert message.by_mouse == True
    assert message.frame._id == 1

    # move down, not hover on any lines
    flamegraph_widget.post_message = MagicMock()
    flamegraph_widget.on_mouse_move(
        MouseMove(
            x=0,
            y=3,
            delta_x=0,
            delta_y=0,
            button=False,
            shift=False,
            meta=False,
            ctrl=False,
        )
    )
    args = flamegraph_widget.post_message.assert_not_called()


def test_flamegraph_render_line_with_some_width_is_0():
    id_store = {}
    root = create_frame(
        {
            "id": 0,
            "values": [10],
            "children": [
                {"id": 2, "values": [3], "children": []},
                {
                    "id": 1,
                    "values": [2],
                    "children": [
                        {"id": 3, "values": [1], "children": []},
                    ],
                },
                {"id": 4, "values": [0.1], "children": []},
            ],
        },
        id_store,
    )

    p = Profile(
        filename="abc",
        root_stack=root,
        highest_lines=1,
        total_sample=2,
        sample_types=[SampleType("samples", "count")],
        id_store=id_store,
    )
    flamegraph_widget = FlameGraph(p, 0, -1, root)
    flamegraph_widget.frame_maps = flamegraph_widget.generate_frame_maps(
        10, focused_stack_id=0
    )

    strip = flamegraph_widget.render_line(
        1,
    )

    line_strings = [seg.text for seg in strip._segments]

    assert line_strings == ["▏", "no", "▏", "n"]


def test_flamegraph_render_line_with_focused_frame():
    id_store = {}
    root = create_frame(
        {
            "id": 0,
            "values": [10],
            "children": [
                {"id": 1, "values": [3], "children": []},
                {"id": 4, "values": [1], "children": []},
                {
                    "id": 2,
                    "values": [6],
                    "children": [
                        {"id": 3, "values": [1], "children": []},
                    ],
                },
            ],
        },
        id_store,
    )

    p = Profile(
        filename="abc",
        root_stack=root,
        highest_lines=1,
        total_sample=2,
        sample_types=[SampleType("samples", "count")],
        id_store=id_store,
    )
    flamegraph_widget = FlameGraph(p, 2, -1, root)
    flamegraph_widget.frame_maps = flamegraph_widget.generate_frame_maps(
        10, focused_stack_id=2
    )

    strip = flamegraph_widget.render_line(
        1,
    )

    line_strings = [seg.text for seg in strip._segments]

    assert line_strings == ["▏", "node-2   "]

    flamegraph_widget.post_message = MagicMock()

    flamegraph_widget.on_mouse_move(
        MouseMove(
            x=0,
            y=1,
            delta_x=0,
            delta_y=0,
            button=False,
            shift=False,
            meta=False,
            ctrl=False,
        )
    )

    flamegraph_widget.post_message.assert_called_once()
    args = flamegraph_widget.post_message.call_args[0]
    message = args[0]
    assert message.by_mouse == True
    assert message.frame._id == 2
