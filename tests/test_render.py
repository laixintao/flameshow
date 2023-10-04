import pytest

from flameshow.pprof_parser import parse_profile
from flameshow.pprof_parser.parser import Line, Profile, SampleType, PprofFrame
from flameshow.render import FlameshowApp
from flameshow.models import Frame


@pytest.mark.asyncio
@pytest.mark.skip(reason="todo rewrite")
async def test_render_goroutine_child_not_100percent_of_parent(data_dir):
    """some goroutines are missing, child is not 100% of parent
    should render 66.6% for the only child in some cases"""
    with open(data_dir / "profile-10seconds.out", "rb") as p:
        profile_data = p.read()

    profile = parse_profile(profile_data, filename="abc")

    app = FlameshowApp(
        profile,
        False,
    )
    async with app.run_test() as pilot:
        app = pilot.app
        parent = app.query_one("#fg-368")
        assert parent.styles.width.value == 100.0
        for i in range(369, 379):
            child = app.query_one(f"#fg-{i}")
            assert child.styles.width.value == 66.67


@pytest.mark.skip(reason="todo rewrite")
def test_default_sample_types_heap():
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
    p.sample_types = [
        SampleType("alloc_objects", "count"),
        SampleType("alloc_space", "bytes"),
        SampleType("inuse_objects", "count"),
        SampleType("inuse_space", "bytes"),
    ]
    app = FlameshowApp(
        p,
        False,
    )
    assert app.sample_index == 3


def test_render_detail_when_parent_zero():
    root = PprofFrame("root", 0, values=[0])
    s1 = PprofFrame("s1", 1, values=[0], parent=root, root=root)
    s1.line = Line()
    s1.line.function.name = "asdf"

    detail = s1.render_detail(0, "bytes")
    assert "(0.0% of parent, 0.0% of root)" in detail
