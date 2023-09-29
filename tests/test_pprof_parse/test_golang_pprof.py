import datetime
import json
import json

import pytest

from flameshow.pprof_parser.parser import ProfileParser
from flameshow.pprof_parser.parser import (
    Function,
    Line,
    Location,
    Mapping,
    ProfileParser,
    parse_profile,
    unmarshal,
    get_frame_tree,
)


def test_python_protobuf_goroutine_check_frame_tree(goroutine_pprof, data_dir):
    profile = parse_profile(goroutine_pprof, "profile10s.out")
    frame_tree = get_frame_tree(profile.root_stack)

    with open(data_dir / "goroutine_frametree.json") as f:
        expected = json.load(f)

    assert frame_tree == expected


def test_golang_goroutine_parse_using_protobuf(goroutine_pprof):
    profile = parse_profile(goroutine_pprof, "goroutine.out")
    assert len(profile.sample_types) == 1

    st = profile.sample_types[0]
    assert st.sample_type == "goroutine"
    assert st.sample_unit == "count"

    assert profile.created_at == datetime.datetime(
        2023, 9, 9, 7, 8, 29, 664363, tzinfo=datetime.timezone.utc
    )

    assert profile.period_type.sample_type == "goroutine"
    assert profile.period_type.sample_unit == "count"
    assert profile.period == 1
    assert profile.default_sample_type_index == -1


def test_golang_profile10s_parse_using_protobuf(profile10s):
    profile = parse_profile(profile10s, "profile10s.out")
    assert len(profile.sample_types) == 2

    st = profile.sample_types[0]
    assert st.sample_type == "samples"
    assert st.sample_unit == "count"
    st = profile.sample_types[1]
    assert st.sample_type == "cpu"
    assert st.sample_unit == "nanoseconds"

    assert profile.created_at == datetime.datetime(
        2023, 9, 9, 7, 8, 29, 866118, tzinfo=datetime.timezone.utc
    )

    assert profile.period_type.sample_type == "cpu"
    assert profile.period_type.sample_unit == "nanoseconds"
    assert profile.period == 10000000

    assert profile.default_sample_type_index == -1


def test_protobuf_parse_gorouting_mapping(goroutine_pprof):
    pb_binary = unmarshal(goroutine_pprof)
    parser = ProfileParser("goroutine.out")
    parser.parse_internal_data(pb_binary)
    assert parser.mappings == {
        1: Mapping(
            id=1,
            memory_start=4194304,
            memory_limit=11280384,
            file_offset=0,
            filename="/usr/bin/node-exporter",
            build_id="",
            has_functions=True,
            has_filenames=False,
            has_line_numbers=False,
            has_inline_frames=False,
        ),
        2: Mapping(
            id=2,
            memory_start=140721318682624,
            memory_limit=140721318690816,
            file_offset=0,
            filename="[vdso]",
            build_id="",
            has_functions=False,
            has_filenames=False,
            has_line_numbers=False,
            has_inline_frames=False,
        ),
        3: Mapping(
            id=3,
            memory_start=18446744073699065856,
            memory_limit=18446744073699069952,
            file_offset=0,
            filename="[vsyscall]",
            build_id="",
            has_functions=False,
            has_filenames=False,
            has_line_numbers=False,
            has_inline_frames=False,
        ),
    }
    assert parser.locations[1] == Location(
        id=1,
        mapping=Mapping(
            id=1,
            memory_start=4194304,
            memory_limit=11280384,
            file_offset=0,
            filename="/usr/bin/node-exporter",
            build_id="",
            has_functions=True,
            has_filenames=False,
            has_line_numbers=False,
            has_inline_frames=False,
        ),
        address=4435364,
        lines=[
            Line(
                line_no=336,
                function=Function(
                    id=1,
                    filename="/usr/local/go/src/runtime/proc.go",
                    name="runtime.gopark",
                    start_line=0,
                    system_name="runtime.gopark",
                ),
            )
        ],
        is_folded=False,
    )
    assert parser.functions[1] == Function(
        id=1,
        filename="/usr/local/go/src/runtime/proc.go",
        name="runtime.gopark",
        start_line=0,
        system_name="runtime.gopark",
    )


@pytest.mark.skip(reason="todo, support json")
def test_parse_sample_location_with_multiple_lines(data_dir):
    parser = ProfileParser("abc")
    with open(data_dir / "sample_location_line_multiple.json") as f:
        content = json.load(f)

    profile = parser.parse(content)
    root = profile.root_stack

    names = []
    while root.children:
        c0 = root.children[0]
        names.append(c0.name)
        root = c0

    assert names == [
        "github.com/prometheus/node_exporter/collector.NodeCollector.Collect.func1",
        "github.com/prometheus/node_exporter/collector.execute",
        "github.com/prometheus/node_exporter/collector.(*meminfoCollector).Update",
        "github.com/prometheus/node_exporter/collector.(*meminfoCollector).getMemInfo",
        "github.com/prometheus/node_exporter/collector.procFilePath",
        "path/filepath.Join",
        "path/filepath.join",
        "strings.Join",
        "strings.(*Builder).Grow",
        "strings.(*Builder).grow",
        "runtime.makeslice",
        "runtime.newstack",
        "runtime.copystack",
        "runtime.gentraceback",
    ]


@pytest.mark.skip(reason="todo, support json")
def test_parse_max_depth_when_have_multiple_lines(data_dir):
    parser = ProfileParser("abc")
    with open(data_dir / "profile10s_node_exporter.json") as f:
        content = json.load(f)

    profile = parser.parse(content)
    assert profile.highest_lines == 26
