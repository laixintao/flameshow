from dataclasses import dataclass
import datetime
import logging
import os
import time
from typing import Tuple

from flameshow.models import Frame, Profile, SampleType
from flameshow.utils import sizeof


logger = logging.getLogger(__name__)


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


class PprofFrame(Frame):
    def __init__(
        self, name, _id, children=None, parent=None, values=None, root=None
    ) -> None:
        super().__init__(name, _id, children, parent, values, root)

        self.line = Line()

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


class ProfileParser:
    def __init__(self, filename):
        self.filename = filename
        self.highest = 0
        self.next_id = 0
        # root must be created first, with id = 0
        # when render, focused ip will be set to 0 by default
        self.root = PprofFrame("root", _id=self.idgenerator())
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

    def parse_single_location(self, location, values, parent) -> Tuple[Frame, Frame]:
        """
        Lines might be multiple, for every line, render to a stack
        returns the first stack, and the last stack (to continue the recurssion)
        """
        head = None
        tail = None
        my_parent = parent
        for line in reversed(location["Line"]):
            name = line["Function"]["Name"]

            stack = PprofFrame(name, self.idgenerator())
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

    def debug_root(self, root: Frame, indent=0):
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


def get_frame_tree(root_frame):
    """
    only for testing and debugging
    """

    def _get_child(frame):
        return {c.name: get_frame_tree(c) for c in frame.children}

    return {"root": _get_child(root_frame)}


def parse_profile(profile_dict, filename):
    parser_obj = ProfileParser(filename=filename)
    t1 = time.time()
    profile = parser_obj.parse(profile_dict)
    logger.info("Max depth: %s", parser_obj.highest)
    t2 = time.time()
    logger.info("parse json files cost %s s", t2 - t1)

    return profile
