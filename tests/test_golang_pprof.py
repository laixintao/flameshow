from flameshow.pprof_parser import parse_golang_profile
from flameshow.pprof_parser.pb_parse import parse_profile


def test_golang_goroutine_parse(goroutine_pprof):
    result = parse_golang_profile(goroutine_pprof)
    assert result["TimeNanos"] == 1694243309664362892
    assert result["SampleType"][0] == {"Type": "goroutine", "Unit": "count"}


def test_golang_goroutine_parse_using_protobuf(goroutine_pprof):
    profile = parse_profile(goroutine_pprof, "goroutine.out")
    assert len(profile.sample_types) == 1
    
    st = profile.sample_types[0]
    assert st.sample_type == "goroutine"
    assert st.sample_unit == "count"
