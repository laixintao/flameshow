from flameshow.parsers.stackcollapse_parser import StackCollapseParser

from ..utils import frame2json


def test_parse_simple_text_data(simple_collapse_data):
    parser = StackCollapseParser("a.txt")
    profile = parser.parse(simple_collapse_data)
    assert profile.highest_lines == 3

    assert frame2json(profile.root_stack) == {
        "root": {
            "children": [{
                "a": {
                    "children": [{
                        "b": {
                            "children": [
                                {"c": {"children": [], "values": [5]}},
                                {"d": {"children": [], "values": [4]}},
                            ],
                            "values": [14],
                        }
                    }],
                    "values": [14],
                }
            }],
            "values": [14],
        },
    }

    assert [f.name for f in profile.id_store.values()] == [
        "root",
        "a",
        "b",
        "c",
        "a",
        "b",
        "c",
        "a",
        "b",
        "d",
        "a",
        "b",
        "c",
        "a",
        "b",
    ]

    assert profile.root_stack.children[0].parent.name == "root"


def test_validate_simple_text_data(simple_collapse_data):
    assert StackCollapseParser.validate(simple_collapse_data)


def test_validate_simple_text_data_not_utf8(simple_collapse_data):
    data = (simple_collapse_data.decode() + "你好").encode("big5")
    assert not StackCollapseParser.validate(data)


def test_validate_simple_text_contains_empty(simple_collapse_data):
    data = (simple_collapse_data.decode() + "\r\n\r\n").encode()
    assert StackCollapseParser.validate(data)


def test_validate_simple_text_data_contains_numbers_somtimes():
    data = b"""
a;b;c 10
5
c 4
10
"""
    assert StackCollapseParser.validate(data)


def test_validate_simple_text_data_notmatch():
    data = b"""
a;b;c 10
c
"""
    assert not StackCollapseParser.validate(data)


def test_validate_simple_text_data_contains_numbers_somtimes_parsing():
    data = b"""
a;b;c 10
5
c 4
10
"""
    profile = StackCollapseParser("a.txt").parse(data)
    assert frame2json(profile.root_stack) == {
        "root": {
            "children": [
                {
                    "a": {
                        "children": [{
                            "b": {
                                "children": [
                                    {"c": {"children": [], "values": [10]}}
                                ],
                                "values": [10],
                            }
                        }],
                        "values": [10],
                    }
                },
                {"c": {"children": [], "values": [4]}},
            ],
            "values": [14],
        }
    }


def test_space_and_numbers_in_stackcollapse_symbols():
    data = b"""
a 1;b 2;c 3 10
"""
    profile = StackCollapseParser("a.txt").parse(data)
    assert frame2json(profile.root_stack) == {
        "root": {
            "children": [{
                "a 1": {
                    "children": [{
                        "b 2": {
                            "children": [
                                {
                                    "c 3": {
                                        "children": [],
                                        "values": [10],
                                    }
                                }
                            ],
                            "values": [10],
                        }
                    }],
                    "values": [10],
                }
            }],
            "values": [10],
        },
    }
