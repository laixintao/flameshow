import logging
import os
import re
from typing import Dict
from flameshow.models import Frame, Profile, SampleType

logger = logging.getLogger(__name__)


class StackCollapseFrame(Frame):
    pass


class StackCollapseParser:
    def __init__(self, filename) -> None:
        self.filename = filename
        self.next_id = 0
        self.root = StackCollapseFrame("root", _id=self.idgenerator())
        self.root.root = self.root

        self.highest = 0
        self.id_store: Dict[int, Frame] = {self.root._id: self.root}

    def idgenerator(self):
        i = self.next_id
        self.next_id += 1

        return i

    def parse(self, text_data):
        profile = Profile(
            filename=self.filename,
            root_stack=self.root,
            highest_lines=self.highest,
            total_sample=len(pbdata.sample),
            sample_types=[SampleType("samples", "count")],
            id_store=self.id_store,
        )
        return profile

    @classmethod
    def validate(cls, content: bytes) -> bool:
        try:
            to_check = content.decode("utf-8")
        except:  # noqa E722
            return False

        # only validate the first 100 lines
        lines = to_check.split(os.linesep)
        to_validate_liens = [
            line.strip() for line in lines[:100] if line.strip()
        ]

        if not to_validate_liens:
            logger.info("The file is empty, skip StackCollapseParser")
            return False

        for line in to_validate_liens:
            if not re.match(r".+\s\d+$", line):
                logger.info(
                    "%s not match regex, not suitable for"
                    " StackCollapseParser!",
                    line,
                )
                return False

        return True
