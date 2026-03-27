class FlamegraphTextualException(Exception):
    """Base exception for flamegraph_textual."""


class ProfileParseException(FlamegraphTextualException):
    """Can not parse the profile."""


class UsageError(FlamegraphTextualException):
    """Usage Error."""


class RenderException(FlamegraphTextualException):
    """Error during flamegraph render."""
