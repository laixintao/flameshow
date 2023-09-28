from dataclasses import dataclass, field
import datetime
import logging
import os
import random
import time
from typing import Dict, Tuple, List
from typing_extensions import Self

from textual.color import Color
from flameshow.utils import sizeof


logger = logging.getLogger(__name__)


class ColorPlatteBase:
    def __init__(self):
        self.assigned_color = {}

    def get_color(self, key):
        if key not in self.assigned_color:
            self.assigned_color[key] = self.assign_color(key)
        return self.assigned_color[key]


class LinaerColorPlatte(ColorPlatteBase):
    def __init__(self, start_color, end_color) -> None:
        super().__init__()
        self.platte = self.generate_platte()
        self.assigned_color = {}
        self.start_color = start_color
        self.end_color = end_color
        self.index = 0

    def assign_color(self, key):
        color = self.platte[self.index]
        self.index += 1
        if self.index == len(self.platte):
            self.index = 0

        return color

    def generate_platte(self):
        color_platte = []
        for factor in range(0, 100, 5):
            color_platte.append(start_color.blend(end_color, factor / 100))
        return color_platte


class FlameGraphRandomColorPlatte(ColorPlatteBase):
    def __init__(self) -> None:
        super().__init__()
        self.assigned_color = {}

    def assign_color(self, key):
        return Color(
            205 + int(50 * random.random()),
            0 + int(230 * random.random()),
            0 + int(55 * random.random()),
        )


start_color = Color.parse("#CD0000")
end_color = Color.parse("#FFE637")
# color_platte = LinaerColorPlatte(start_color, end_color)
color_platte = FlameGraphRandomColorPlatte()


class Stack:
    def __init__(
        self, name, _id, children=None, parent=None, values=None, root=None
    ) -> None:
        self.name = name
        self._id = _id
        if children:
            self.children = children
        else:
            self.children = []
        self.parent = parent
        if not values:
            self.values = []
        else:
            self.values = values

        parts = self.name.split("/")
        if len(parts) > 1:
            self.golang_package = "/".join(parts[:-1])
        else:
            self.golang_package = "buildin"

        self.golang_module_function = parts[-1]
        self.golang_module = self.golang_module_function.split(".")[0]

        self.display_name = self.golang_module_function
        self.display_color = color_platte.get_color(self.golang_module)

        self.mapping_file = ""
        self.root = root

    def pile_up(self, childstack: Self):
        childstack.parent = self

        for exist_child in self.children:
            # added to exist, no need to create one
            if exist_child.name == childstack.name:
                # some cases, childstack.children total value not equal to childstack.values
                # so, we need to add values of "parent" instead of add values by every child
                exist_child.values = list(
                    map(sum, zip(exist_child.values, childstack.values))
                )

                for new_child in childstack.children:
                    exist_child.pile_up(new_child)
                return

        self.children.append(childstack)

    def __eq__(self, other):
        if isinstance(other, Stack):
            return self._id == other._id
        return False

    def render_detail(self, sample_index: int, sample_unit: str):
        raise NotImplementedError

    def render_title(self) -> str:
        raise NotImplementedError


@dataclass
class SampleType:
    sample_type: str = ""
    sample_unit: str = ""


@dataclass
class Profile:
    filename: str = ""
    root_stack: Stack | None = None
    highest_lines: int = 0
    total_sample: int = 0
    created_at: datetime.datetime | None = None
    id_store: Dict[int, Stack] = field(default_factory=dict)
    sample_types: List[SampleType] = field(default_factory=list)
