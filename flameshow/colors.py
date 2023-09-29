import random
import logging

from textual.color import Color

logger = logging.getLogger(__name__)


class ColorPlatteBase:
    def __init__(self):
        self.assigned_color = {}

    def get_color(self, key):
        if key not in self.assigned_color:
            self.assigned_color[key] = self.assign_color(key)
        return self.assigned_color[key]

    def assign_color(self, key):
        raise NotImplementedError


class LinaerColorPlatte(ColorPlatteBase):
    def __init__(
        self,
        start_color=Color.parse("#CD0000"),
        end_color=Color.parse("#FFE637"),
    ) -> None:
        super().__init__()
        self.assigned_color = {}
        self.start_color = start_color
        self.end_color = end_color
        self.index = 0
        self.platte = self.generate_platte()

    def assign_color(self, key):
        color = self.platte[self.index]
        self.index += 1
        if self.index == len(self.platte):
            self.index = 0

        logger.debug("assign color=%s", color)
        return color

    def generate_platte(self):
        color_platte = []
        for factor in range(0, 100, 5):
            color_platte.append(
                self.start_color.blend(self.end_color, factor / 100)
            )
        return color_platte


class FlameGraphRandomColorPlatte(ColorPlatteBase):
    def __init__(self) -> None:
        super().__init__()
        self.assigned_color = {}

    def assign_color(self, *args):
        return Color(
            205 + int(50 * random.random()),
            0 + int(230 * random.random()),
            0 + int(55 * random.random()),
        )


flamegraph_random_color_platte = FlameGraphRandomColorPlatte()
linaer_color_platte = LinaerColorPlatte()
