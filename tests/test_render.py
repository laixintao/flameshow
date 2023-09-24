import pytest
from flameshow.parser import ProfileParser
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
