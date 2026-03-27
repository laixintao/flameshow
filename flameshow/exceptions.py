from flamegraph_textual.exceptions import (
    ProfileParseException,
    RenderException,
)


class FlameshowException(Exception):
    """FlameShow base Exception"""


class UsageError(FlameshowException):
    """Usage Error"""


__all__ = [
    "FlameshowException",
    "ProfileParseException",
    "UsageError",
    "RenderException",
]
