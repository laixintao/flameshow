import pytest
from flameshow.pprof_parser.parser import Profile, ProfileParser, SampleType
from flameshow.render import FlameGraphApp
from flameshow.pprof_parser import parse_golang_profile


@pytest.mark.asyncio
async def test_render_goroutine_child_not_100percent_of_parent(data_dir):
    """some goroutines are missing, child is not 100% of parent
    should render 66.6% for the only child in some cases"""
    with open(data_dir / "profile-10seconds.out", "rb") as p:
        profile_data = p.read()

    profile_dict = parse_golang_profile(profile_data)
    parser_obj = ProfileParser(filename="abc")
    profile = parser_obj.parse(profile_dict)

    app = FlameGraphApp(
        profile,
        15,
        False,
    )
    async with app.run_test() as pilot:
        app = pilot.app
        parent = app.query_one("#fg-368")
        assert parent.styles.width.value == 100.0
        for i in range(369, 379):
            child = app.query_one(f"#fg-{i}")
            assert child.styles.width.value == 66.67


def test_default_sample_types_heap():
    p = Profile()
    app = FlameGraphApp(
        Profile(),
        15,
        False,
    )
    p.sample_types = [
        SampleType("alloc_objects", "count"),
        SampleType("alloc_space", "bytes"),
        SampleType("inuse_objects", "count"),
        SampleType("inuse_space", "bytes"),
    ]
    assert app._choose_default_index(p.sample_types) == 3


def test_default_sample_types_profile():
    p = Profile()
    app = FlameGraphApp(
        Profile(),
        15,
        False,
    )
    p.sample_types = [
        SampleType("samples", "count"),
        SampleType("cpu", "nanoseconds"),
    ]
    assert app._choose_default_index(p.sample_types) == 0
