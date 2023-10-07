from flameshow.colors import LinaerColorPlatte, flamegraph_random_color_platte
from textual.color import Color


def test_linaer_color_platte():
    platte = LinaerColorPlatte()

    color1 = platte.get_color("1")
    color3 = platte.get_color("1")

    color2 = platte.get_color("2")
    assert color1 is color3

    assert isinstance(color2, Color)

    for key in range(999):
        platte.get_color(key)


def test_flamegraph_random_color_platte():
    platte = flamegraph_random_color_platte

    color1 = platte.get_color("1")
    color3 = platte.get_color("1")

    color2 = platte.get_color("2")
    assert color1 is color3

    assert isinstance(color2, Color)
