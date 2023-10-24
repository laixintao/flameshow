import logging
from flameshow.exceptions import ProfileParseException

from flameshow.pprof_parser.parser import ProfileParser as PprofParser

from .stackcollapse_parser import StackCollapseParser

logger = logging.getLogger(__name__)


ALL_PARSERS = [PprofParser, StackCollapseParser]


def choose_parser(content: bytes):
    for p in ALL_PARSERS:
        if p.validate(content):
            return p
    raise ProfileParseException("Can not match any parser")


def parse(filecontent: bytes, filename):
    parser_cls = choose_parser(filecontent)
    logger.info("Using %s...", parser_cls)
    parser = parser_cls(filename)
    profile = parser.parse(filecontent)
    return profile
