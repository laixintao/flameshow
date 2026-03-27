class FlameshowException(Exception):
    """FlameShow base Exception"""


class UsageError(FlameshowException):
    """Usage Error"""


from flamegraph_textual.exceptions import ProfileParseException, RenderException

__all__ = [
    "FlameshowException",
    "ProfileParseException",
    "UsageError",
    "RenderException",
]
