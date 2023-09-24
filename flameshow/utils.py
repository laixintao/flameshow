def fgid(_id: int) -> str:
    return f"fg-{_id}"


def intid(_fgid: str) -> int:
    return int(_fgid.split("-")[1])
