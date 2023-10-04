from flameshow.utils import sizeof


def test_sizeof():
    assert sizeof(1) == "1.0B"
    assert sizeof(2048) == "2.0KiB"
    assert (
        sizeof(5.83 * 1024 * 1024 * 1024 * 1024 * 1024 * 1024 * 1024 * 1024)
        == "5.8YiB"
    )
