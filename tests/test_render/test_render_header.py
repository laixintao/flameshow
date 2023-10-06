from rich.text import Text, Span
from flameshow.render.header import (
    HeaderIcon,
    HeaderTitle,
    HeaderOpenedFilename,
    FlameshowHeader,
)


def test_header_icon():
    hi = HeaderIcon()

    assert hi.render() == "🔥"


def test_header_title():
    ht = HeaderTitle()
    ht.text = "abc"
    ht.sub_text = "foo"

    assert ht.render() == Text("abc — foo", spans=[Span(6, 9, "dim")])


def test_header_opened_filename():
    hf = HeaderOpenedFilename("goro.out")

    assert hf.render() == Text("goro.out")


def test_flameshow_header():
    fh = FlameshowHeader("foo.out")
    result = list(fh.compose())

    assert len(result) == 2

    header_center_text = result[1]._nodes[1]

    assert isinstance(header_center_text, HeaderOpenedFilename)
