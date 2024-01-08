import logging
import os
import re
from typing import Dict

from rich.text import Text

from flameshow.models import Frame, Profile, SampleType

logger = logging.getLogger(__name__)


class StackCollapseFrame(Frame):
    def render_one_frame_detail(
        self, frame, sample_index: int, sample_unit: str
    ):
        return [Text(f"{frame.name}\n")]


class StackCollapseParser:
    def __init__(self, filename) -> None:
        self.filename = filename
        self.next_id = 0
        self.root = StackCollapseFrame(
            "root", _id=self.idgenerator(), values=[0]
        )
        self.root.root = self.root

        self.highest = 0
        self.id_store: Dict[int, Frame] = {self.root._id: self.root}
        self.line_regex = r"(.*?) (\d+)$"
        self.line_matcher = re.compile(self.line_regex)

    def idgenerator(self):
        i = self.next_id
        self.next_id += 1

        return i

    def parse(self, text_data):
        text_data = text_data.decode()
        lines = text_data.split(os.linesep)
        for line in lines:
            self.parse_line(line)

        logger.info("root: %s, %s", self.root, self.root.values)
        logger.debug("root.children: %s", self.root.children)

        profile = Profile(
            filename=self.filename,
            root_stack=self.root,
            highest_lines=self.highest,
            total_sample=len(lines),
            sample_types=[SampleType("samples", "count")],
            id_store=self.id_store,
        )
        logger.info("profile.lines = %s", profile.lines)
        logger.info("profile.id_store = %s", profile.id_store)
        return profile

    def parse_line(self, line) -> None:
        line = line.strip()
        if not line:
            return
        matcher = self.line_matcher.match(line)
        if not matcher:
            logger.warn(
                "Can not parse {} with regex {}".format(line, self.line_regex)
            )
            return
        frame_str = matcher.group(1)
        count = int(matcher.group(2))
        frame_names = frame_str.split(";")
        logger.info("frame names:%s, count: %s", frame_names, count)

        pre = None
        head = None
        for name in frame_names:
            frame = StackCollapseFrame(
                name,
                self.idgenerator(),
                children=[],
                parent=pre,
                values=[count],
                root=self.root,
            )
            self.id_store[frame._id] = frame
            if pre:
                pre.children = [frame]
                frame.parent = pre
            if not head:
                head = frame
            pre = frame

        if head:
            self.root.pile_up(head)
            self.root.values[0] += head.values[0]

        if len(frame_names) > self.highest:
            self.highest = len(frame_names)
        logger.debug("over")

    @classmethod
    def validate(cls, content: bytes) -> bool:
        try:
            to_check = content.decode("utf-8")
        except:  # noqa E722
            return False

        # only validate the first 100 lines
        lines = to_check.split(os.linesep)
        to_validate_lines = [
            line.strip() for line in lines[:100] if line.strip()
        ]

        if not to_validate_lines:
            logger.info("The file is empty, skip StackCollapseParser")
            return False

        for index, line in enumerate(to_validate_lines):
            if not re.match(r"(.* )?\d+", line):
                logger.info(
                    "line %d not match regex, line:%s not suitable for"
                    " StackCollapseParser!",
                    index + 1,
                    line,
                )
                return False

        return True
