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


@dataclass
class Line:
    line_no: int = 0
    function_filename: str = ""
    function_id: int = 0
    function_name: str = ""
    function_start_line: int = 0
    function_system_name: str = ""

    @classmethod
    def from_dict(cls, data):
        function = data.get("Function", {})
        return cls(
            line_no=data.get("Line"),
            function_filename=function.get("Filename"),
            function_id=function.get("ID"),
            function_name=function.get("Name"),
            function_start_line=function.get("StartLine"),
            function_system_name=function.get("SystemName"),
        )


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

        self.line = Line()

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

    def humanize(self, sample_unit, value):
        display_value = value
        if sample_unit == "bytes":
            display_value = sizeof(value)

        return display_value

    def render_detail(self, sample_index: int, sample_unit: str):
        """
        render 2 lines of detail information
        """
        if self._id == 0:  # root
            total = sum([c.values[sample_index] for c in self.children])
            line1 = f"Total: {self.humanize(sample_unit, total)}"
            line2 = ""
            if self.children:
                line2 = f"Binary: {self.children[0].mapping_file}"
        else:
            line1 = f"{self.line.function_filename}, [b]line {self.line.line_no}[/b]"
            if not self.parent or not self.root:
                logger.warning("self.parent or self.root is None!")
                line2 = "<error>"
            else:
                if not self.parent.values[sample_index]:
                    p_parent = 0
                else:
                    p_parent = (
                        self.values[sample_index]
                        / self.parent.values[sample_index]
                        * 100
                    )

                if not self.root.values[sample_index]:
                    p_root = 0
                else:
                    p_root = (
                        self.values[sample_index] / self.root.values[sample_index] * 100
                    )

                value = self.humanize(sample_unit, self.values[sample_index])
                line2 = (
                    f"{self.line.function_name}: [b red]{value}[/b"
                    f" red] ({p_parent:.1f}% of parent, {p_root:.1f}% of root)"
                )
        return line1 + os.linesep + line2

    def render_title(self) -> str:
        return self.display_name


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


class ProfileParser:
    def __init__(self, filename):
        self.filename = filename
        self.highest = 0
        self.next_id = 0
        # root must be created first, with id = 0
        # when render, focused ip will be set to 0 by default
        self.root = Stack("root", _id=self.idgenerator())
        self.total_sample = 0
        self.id_store = {self.root._id: self.root}

    def idgenerator(self):
        i = self.next_id
        self.next_id += 1

        return i

    def parse_sample(self, sample, parent):
        locations = sample["Location"]

        locations_reverse = reversed(locations)

        my_depth = sum(len(location["Line"]) for location in locations)

        self.highest = max(my_depth, self.highest)

        stack = self.parse_location(
            locations_reverse, values=sample["Value"], parent=parent
        )
        return stack

    def parse_location(self, locations, values, parent):
        """
        recursive parse locations
        """
        location1, *rest = locations

        head, tail = self.parse_single_location(location1, values, parent)

        if rest:
            tail.children = [self.parse_location(rest, values, tail)]
        else:
            tail.children = []

        return head

    def parse_single_location(self, location, values, parent) -> Tuple[Stack, Stack]:
        """
        Lines might be multiple, for every line, render to a stack
        returns the first stack, and the last stack (to continue the recurssion)
        """
        head = None
        tail = None
        my_parent = parent
        for line in reversed(location["Line"]):
            name = line["Function"]["Name"]

            stack = Stack(name, self.idgenerator())
            self.id_store[stack._id] = stack
            stack.values = values
            stack.parent = my_parent
            stack.root = self.root

            stack.line = Line.from_dict(line)

            stack.mapping_file = location["Mapping"]["File"]

            my_parent = stack
            if not head:
                head = stack
            if tail:
                tail.children = [stack]

            tail = stack

        return head, tail

    def debug_root(self, root: Stack, indent=0):
        num = str(indent)
        space = num + " " * (indent - len(num))
        logger.debug(f"{space}{root.name=} ({root.values})")
        for child in root.children:
            self.debug_root(child, indent + 2)

    def parse(self, data: dict):
        samples = data["Sample"]
        sample_types = [SampleType(t["Type"], t["Unit"]) for t in data["SampleType"]]

        self.total_sample = len(samples)

        root = self.root
        root.values = [0] * len(sample_types)
        start = time.time()
        for sample in samples:
            child_stack = self.parse_sample(sample, parent=root)

            root.values = list(map(sum, zip(root.values, child_stack.values)))
            root.pile_up(child_stack)

        end = time.time()
        logger.info("Parse profile cost %.2fs", end - start)

        profile = Profile(
            filename=self.filename,
            root_stack=root,
            highest_lines=self.highest,
            total_sample=self.total_sample,
            id_store=self.id_store,
            sample_types=sample_types,
        )

        created_at = data.get("TimeNanos")
        if created_at:
            date = datetime.datetime.fromtimestamp(created_at / 1e9)
            profile.created_at = date
        return profile
