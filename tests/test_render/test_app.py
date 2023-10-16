from textual.geometry import Size
from flameshow.models import Frame, Profile, SampleType
from flameshow.render.app import FlameGraphScroll, FlameshowApp
from unittest.mock import MagicMock, patch, PropertyMock


def test_flamegraph_container_scroll():
    def _test_scroll(line_no, height, expected_center):
        fc = FlameGraphScroll()
        size = MagicMock()
        size.height = height

        with patch(
            "flameshow.render.app.FlameGraphScroll.size",
            new_callable=PropertyMock,
        ) as mock_size:
            mock_size.return_value = Size(0, height)
            to_line = fc.scroll_to_make_line_center(line_no)

        assert to_line == expected_center

    _test_scroll(line_no=0, height=10, expected_center=0)
    _test_scroll(line_no=3, height=10, expected_center=0)
    _test_scroll(line_no=4, height=10, expected_center=0)
    _test_scroll(line_no=5, height=10, expected_center=0)
    _test_scroll(line_no=6, height=10, expected_center=1)
    _test_scroll(line_no=10, height=10, expected_center=5)
    _test_scroll(line_no=20, height=10, expected_center=15)


def test_app_set_title_after_mount():
    r = Frame("root", 0)
    p = Profile(
        filename="abc",
        root_stack=r,
        highest_lines=1,
        total_sample=2,
        sample_types=[SampleType("goroutine", "count")],
        id_store={},
    )
    app = FlameshowApp(p)
    app.on_mount()
    assert app.title == "flameshow"
    assert app.sub_title.startswith("v")
    assert app.view_frame == r
    assert app.sample_unit == "count"
