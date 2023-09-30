from dataclasses import dataclass, field
import datetime
import logging
from typing import Dict, List
from typing_extensions import Self

from .runtime import r


logger = logging.getLogger(__name__)


class Frame:
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

        golang_module_function = parts[-1]
        golang_module = golang_module_function.split(".")[0]

        self.display_name = golang_module_function
        self.color_key = golang_module

        self.mapping_file = ""
        self.root = root

    def pile_up(self, childstack: Self):
        childstack.parent = self

        for exist_child in self.children:
            # added to exist, no need to create one
            if exist_child.name == childstack.name:
                # some cases, childstack.children total value not equal to
                # childstack.values
                # so, we need to add values of "parent" instead of add values
                # by every child
                exist_child.values = list(
                    map(sum, zip(exist_child.values, childstack.values))
                )

                for new_child in childstack.children:
                    exist_child.pile_up(new_child)
                return

        self.children.append(childstack)

    def __eq__(self, other):
        if isinstance(other, Frame):
            return self._id == other._id
        return False

    def render_detail(self, sample_index: int, sample_unit: str):
        raise NotImplementedError

    def render_title(self) -> str:
        raise NotImplementedError

    @property
    def display_color(self):
        return r.get_color(self.color_key)

    def __repr__(self) -> str:
        return f"<Frame {self.name}>"


@dataclass
class SampleType:
    sample_type: str = ""
    sample_unit: str = ""


@dataclass
class Profile:
    filename: str = ""

    created_at: datetime.datetime | None = None
    id_store: Dict[int, Frame] = field(default_factory=dict)

    sample_types: List[SampleType] = field(default_factory=list)
    default_sample_type_index: int = -1

    period_type: SampleType | None = None
    period: int = 0

    # TODO parse using protobuf
    root_stack: Frame | None = None
    highest_lines: int = 0
    total_sample: int = 0
