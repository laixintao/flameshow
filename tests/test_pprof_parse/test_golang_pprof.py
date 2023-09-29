import datetime
import json

from flameshow.pprof_parser import parse_golang_profile
from flameshow.pprof_parser.parser import (
    get_frame_tree,
    parse_profile as golang_parse_profile,
)
from flameshow.pprof_parser.pb_parse import parse_profile


def test_golang_goroutine_parse(goroutine_pprof):
    result = parse_golang_profile(goroutine_pprof)
    assert result["TimeNanos"] == 1694243309664362892
    assert result["SampleType"][0] == {"Type": "goroutine", "Unit": "count"}


def test_golang_goroutine_check_frame_tree(goroutine_pprof, data_dir):
    bdata = parse_golang_profile(goroutine_pprof)
    result = golang_parse_profile(bdata, "goroutine.out")
    frame_tree = get_frame_tree(result.root_stack)

    with open(data_dir / "goroutine_frametree.json") as f:
        expected = json.load(f)

    assert frame_tree == expected


def test_golang_goroutine_parse_using_protobuf(goroutine_pprof):
    profile = parse_profile(goroutine_pprof, "goroutine.out")
    assert len(profile.sample_types) == 1

    st = profile.sample_types[0]
    assert st.sample_type == "goroutine"
    assert st.sample_unit == "count"

    assert profile.created_at == datetime.datetime(2023, 9, 9, 15, 8, 29, 664363)

    assert profile.period_type.sample_type == "goroutine"
    assert profile.period_type.sample_unit == "count"
    assert profile.period == 1
    assert profile.default_sample_type_index == -1


def test_golang_profile10s_parse_using_protobuf(profile10s):
    profile = parse_profile(profile10s, "profile10s.json")
    assert len(profile.sample_types) == 2

    st = profile.sample_types[0]
    assert st.sample_type == "samples"
    assert st.sample_unit == "count"
    st = profile.sample_types[1]
    assert st.sample_type == "cpu"
    assert st.sample_unit == "nanoseconds"

    assert profile.created_at == datetime.datetime(2023, 9, 9, 15, 8, 29, 866118)

    assert profile.period_type.sample_type == "cpu"
    assert profile.period_type.sample_unit == "nanoseconds"
    assert profile.period == 10000000

    assert profile.default_sample_type_index == -1
