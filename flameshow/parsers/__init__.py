from binaryornot.helpers import is_binary_string
from flameshow.pprof_parser.parser import ProfileParser as PprofParser

from .stackcollapse_parser import StackCollapseParser


def choose_parser(content):
    to_check = content[:1024]
    if is_binary_string(to_check):
        return PprofParser
    return StackCollapseParser


def parse(filecontent, filename):
    parser_cls = choose_parser(filecontent)
    parser = parser_cls(filename)
    profile = parser.parse(filecontent)
    return profile
