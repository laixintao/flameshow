class FlameshowException(Exception):
    """FlameShow base Exception"""


class ProfileParseException(FlameshowException):
    """Can not parse the profile"""


class UsageError(FlameshowException):
    """Usage Error"""


class RenderException(FlameshowException):
    """Got error when render, this usually means code bug of Flameshow, you can open an issue"""  # noqa: E501
