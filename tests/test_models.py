from unittest.mock import patch


from flameshow.models import Profile, SampleType
from flameshow.pprof_parser.parser import Frame, PprofFrame, ProfileParser


def test_parse_max_depth_when_have_multiple_lines(profile10s):
    parser = ProfileParser("abc")

    profile = parser.parse(profile10s)
    assert profile.highest_lines == 26


def test_pile_up():
    root = Frame("root", 0, values=[5])
    s1 = Frame("s1", 1, values=[4], parent=root)
    s2 = Frame("s2", 2, values=[4], parent=s1)

    root.children = [s1]
    s1.children = [s2]

    s1 = Frame("s1", 3, values=[3], parent=None)
    s2 = Frame("s2", 4, values=[2], parent=s1)
    s1.children = [s2]

    root.pile_up(s1)
    assert root.children[0].values == [7]
    assert root.children[0].children[0].values == [6]


def test_profile_creataion():
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
    assert p.lines == [[root], [s1], [s2, s3]]


def test_frame():
    f1 = Frame("foo", 12)
    f2 = Frame("bar", 12)

    assert f1 == f2
    assert f1 != Frame("a", 13)
    assert f1 != 123

    f4 = Frame("has_child", 14, [f1])
    assert f4.children == [f1]

    assert str(f1) == "<Frame #12 foo>"


def test_frame_get_color():
    with patch("flameshow.models.r") as mock_r:
        mock_r.get_color.return_value = "#1122ff"
        f1 = Frame("foo", 12)
        assert f1.display_color == "#1122ff"
        mock_r.get_color.assert_called_with("foo")


def test_frame_get_color_full_model_path():
    with patch("flameshow.models.r") as mock_r:
        mock_r.get_color.return_value = "#1122ff"
        f1 = PprofFrame(
            "github.com/prometheus/common/expfmt.MetricFamilyToText.func1", 12
        )
        assert f1.display_color == "#1122ff"
        mock_r.get_color.assert_called_with("expfmt")
