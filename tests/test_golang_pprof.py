from flameshow.pprof_parser import parse_golang_profile


def test_golang_goroutine_parse(goroutine_pprof):
    result = parse_golang_profile(goroutine_pprof)
    assert result["TimeNanos"] == 1694243309664362892
    assert result["SampleType"][0] == {
           "Type": "goroutine",
           "Unit": "count"
         }

