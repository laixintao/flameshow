from flameshow.pprof_parser.parser import Line, Profile, SampleType, PprofFrame
from flameshow.models import Frame
from flameshow.render.flamegraph import FlameGraph, add_array, FrameMap


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


def test_render_detail_when_parent_zero():
    root = PprofFrame("root", 0, values=[0])
    s1 = PprofFrame("s1", 1, values=[0], parent=root, root=root)
    s1.line = Line()
    s1.line.function.name = "asdf"

    detail = s1.render_detail(0, "bytes")
    assert "(0.0% of parent, 0.0% of root)" in detail


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
    flamegraph_widget = FlameGraph(p, 0, -1, 0)
    flamegraph_widget.frame_maps = flamegraph_widget.generate_frame_maps(
        10, focused_stack_id=0
    )

    strip = flamegraph_widget.render_line(
        1,
    )

    line_strings = [seg.text for seg in strip._segments]

    assert line_strings == ["▏", "s1 ", "▏", "s2"]
