from rich.text import Text
from flameshow.parsers.stackcollapse_parser import StackCollapseFrame


def test_frame_model_render():
    f = StackCollapseFrame(
        "java::abc", 1, parent=None, children=[], values=[13]
    )
    render_result = f.render_one_frame_detail(f, 0, "count")
    assert len(render_result) == 1
    item = render_result[0]
    assert item.markup == "java::abc\n"


def test_frame_model_render_with_square():
    f = StackCollapseFrame("[abc]", 1, parent=None, children=[], values=[13])
    render_result = f.render_one_frame_detail(f, 0, "count")
    assert len(render_result) == 1
    item = render_result[0]
    assert item.markup == "\\[abc]\n"

    title = f.title
    assert isinstance(title, Text)
    assert title.plain == "[abc]"
