"""
Parse golang's pprof format into flameshow.models which can be rendered.

Ref:
https://github.com/google/pprof/tree/main/proto
"""

from dataclasses import dataclass, field
import datetime
import gzip
import logging
from typing import Dict, List

from rich.text import Text

from flameshow.models import Frame, Profile, SampleType

from . import profile_pb2

logger = logging.getLogger(__name__)


@dataclass
class Function:
    id: int = 0
    filename: str = ""
    name: str = ""
    start_line: int = 0
    system_name: str = ""


@dataclass
class Line:
    line_no: int = 0
    function: Function = field(default_factory=Function)


@dataclass
class Mapping:
    id: int = 0
    memory_start: int = 0
    memory_limit: int = 0
    file_offset: int = 0

    filename: str = ""
    build_id: str = ""

    has_functions: bool | None = None
    has_filenames: bool | None = None
    has_line_numbers: bool | None = None
    has_inline_frames: bool | None = None


@dataclass
class Location:
    id: int = 0
    mapping: Mapping = field(default_factory=Mapping)
    address: int = 0
    lines: List[Line] = field(default_factory=list)
    is_folded: bool = False


class PprofFrame(Frame):
    def __init__(
        self,
        name,
        _id,
        children=None,
        parent=None,
        values=None,
        root=None,
        line=None,
        mapping=None,
    ) -> None:
        super().__init__(name, _id, children, parent, values, root)

        parts = self.name.split("/")
        if len(parts) > 1:
            self.golang_package = "/".join(parts[:-1])
        else:
            self.golang_package = "buildin"

        self.golang_module_function = parts[-1]

        self.golang_module = self.golang_module_function.split(".")[0]

        self.mapping_file = ""
        self.line = line
        self.mapping = mapping

    @property
    def color_key(self):
        return self.golang_module

    @property
    def display_name(self):
        return self.golang_module_function

    def render_one_frame_detail(self, frame, sample_index, sample_unit):
        if frame._id == 0:  # root
            total = sum([c.values[sample_index] for c in frame.children])
            value = frame.humanize(sample_unit, total)
            if frame.children:
                binary_name = f"Binary: {frame.children[0].mapping.filename}"
            else:
                binary_name = "root"
            detail = f"{binary_name} [b red]{value}[/b red]\n"
            return [detail]

        value = frame.humanize(sample_unit, frame.values[sample_index])
        line1 = f"{frame.line.function.name}: [b red]{value}[/b red]\n"

        line2 = (
            f"  [grey37]{frame.line.function.filename}, [b]line"
            f" {frame.line.line_no}[/b][/grey37]\n"
        )
        return [Text.from_markup(line1), Text.from_markup(line2)]

    @property
    def title(self) -> str:
        return self.display_name


def unmarshal(content) -> profile_pb2.Profile:
    if len(content) < 2:
        raise Exception(
            "Profile content length is too short: {} bytes".format(
                len(content)
            )
        )
    is_gzip = content[0] == 31 and content[1] == 139

    if is_gzip:
        content = gzip.decompress(content)

    profile = profile_pb2.Profile()
    profile.ParseFromString(content)

    return profile


class ProfileParser:
    def __init__(self, filename):
        self.filename = filename
        # uniq id
        self.next_id = 0

        self.root = PprofFrame("root", _id=self.idgenerator())
        # need to set PprofFrame.root for every frame
        self.root.root = self.root

        # store the pprof's string table
        self._t = []
        # parse cached locations, profile do not need this, so only store
        # them on the parser
        self.locations = []
        self.highest = 0

        self.id_store: Dict[int, Frame] = {self.root._id: self.root}

    def idgenerator(self):
        i = self.next_id
        self.next_id += 1

        return i

    def s(self, index):
        return self._t[index]

    def parse_internal_data(self, pbdata):
        self._t = pbdata.string_table
        self.functions = self.parse_functions(pbdata.function)
        self.mappings = self.parse_mapping(pbdata.mapping)
        self.locations = self.parse_location(pbdata.location)

    def parse(self, binary_data):
        pbdata = unmarshal(binary_data)
        self.parse_internal_data(pbdata)

        sample_types = self.parse_sample_types(pbdata.sample_type)

        root = self.root
        root.values = [0] * len(sample_types)
        for pbsample in pbdata.sample:
            child_frame = self.parse_sample(pbsample)
            if not child_frame:
                continue
            root.values = list(map(sum, zip(root.values, child_frame.values)))
            root.pile_up(child_frame)

        pprof_profile = Profile(
            filename=self.filename,
            root_stack=root,
            highest_lines=self.highest,
            total_sample=len(pbdata.sample),
            sample_types=sample_types,
            id_store=self.id_store,
        )

        # default is 0, by the doc, default should be the last one
        if pbdata.default_sample_type:
            pprof_profile.default_sample_type_index = (
                pbdata.default_sample_type
            )

        pprof_profile.created_at = self.parse_created_at(pbdata.time_nanos)
        pprof_profile.period = pbdata.period
        pprof_profile.period_type = self.to_smaple_type(pbdata.period_type)

        return pprof_profile

    def parse_sample(self, sample) -> PprofFrame | None:
        values = sample.value
        locations = list(
            reversed([self.locations[i] for i in sample.location_id])
        )

        my_depth = sum(len(loc.lines) for loc in locations)
        self.highest = max(my_depth, self.highest)

        current_parent = None
        head = None
        for location in locations:
            for line in location.lines:
                frame = self.line2frame(location, line, values)

                if current_parent:
                    frame.parent = current_parent
                    current_parent.children = [frame]
                if not head:
                    head = frame

                current_parent = frame

        return head

    def line2frame(self, location: Location, line: Line, values) -> PprofFrame:
        frame = PprofFrame(
            name=line.function.name,
            _id=self.idgenerator(),
            values=values,
            root=self.root,
            mapping=location.mapping,
        )
        frame.line = line
        self.id_store[frame._id] = frame
        return frame

    def parse_location(self, pblocations):
        parsed_locations = {}
        for pl in pblocations:
            loc = Location()
            loc.id = pl.id
            loc.mapping = self.mappings[pl.mapping_id]
            loc.address = pl.address
            loc.lines = self.parse_line(pl.line)
            loc.is_folded = pl.is_folded
            parsed_locations[loc.id] = loc

        return parsed_locations

    def parse_mapping(self, pbmappings):
        mappings = {}
        for pbm in pbmappings:
            m = Mapping()
            m.id = pbm.id
            m.memory_start = pbm.memory_start
            m.memory_limit = pbm.memory_limit
            m.file_offset = pbm.file_offset
            m.filename = self.s(pbm.filename)
            m.build_id = self.s(pbm.build_id)
            m.has_functions = pbm.has_functions
            m.has_filenames = pbm.has_filenames
            m.has_line_numbers = pbm.has_line_numbers
            m.has_inline_frames = pbm.has_inline_frames

            mappings[m.id] = m

        return mappings

    def parse_line(self, pblines) -> List[Line]:
        lines = []
        for pl in reversed(pblines):
            line = Line(
                line_no=pl.line,
                function=self.functions[pl.function_id],
            )
            lines.append(line)
        return lines

    def parse_functions(self, pfs):
        functions = {}
        for pf in pfs:
            functions[pf.id] = Function(
                id=pf.id,
                filename=self.s(pf.filename),
                name=self.s(pf.name),
                system_name=self.s(pf.system_name),
                start_line=pf.start_line,
            )
        return functions

    def parse_created_at(self, time_nanos):
        date = datetime.datetime.fromtimestamp(
            time_nanos / 1e9, tz=datetime.timezone.utc
        )
        return date

    def parse_sample_types(self, sample_types):
        result = []
        for st in sample_types:
            result.append(self.to_smaple_type(st))

        return result

    def to_smaple_type(self, st):
        return SampleType(self.s(st.type), self.s(st.unit))

    @classmethod
    def validate(cls, content: bytes) -> bool:
        try:
            unmarshal(content)
        except:  # noqa E722
            logger.info("Error when parse content as Pprof")
            return False
        return True


def get_frame_tree(root_frame):
    """
    only for testing and debugging
    """

    def _get_child(frame):
        return {c.name: _get_child(c) for c in frame.children}

    return {"root": _get_child(root_frame)}


def parse_profile(binary_data, filename):
    parser = ProfileParser(filename)
    profile = parser.parse(binary_data)

    # import ipdb; ipdb.set_trace()
    return profile


if __name__ == "__main__":
    with open("tests/pprof_data/goroutine.out", "rb") as f:
        content = f.read()

    parse_profile(content, "abc")
