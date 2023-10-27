from flameshow.parsers.stackcollapse_parser import StackCollapseFrame


def test_frame_model_render():
    f = StackCollapseFrame(
        "java::abc", 1, parent=None, children=[], values=[13]
    )
    render_result = f.render_one_frame_detail(f, 0, "count")
    assert render_result == ["java::abc\n"]
