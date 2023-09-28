from .colors import flamegraph_random_color_platte
from dataclasses import dataclass


@dataclass
class Runtime:
    color_platte = flamegraph_random_color_platte

    def get_color(self, key):
        return self.color_platte.get_color(key)


r = Runtime()
