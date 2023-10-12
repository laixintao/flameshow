import pytest
import pathlib
from flameshow.pprof_parser import parse_profile
from flameshow.models import Frame


pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session")
def data_dir():
    return pathlib.Path(__file__).parent / "pprof_data"


@pytest.fixture(scope="session")
def goroutine_pprof():
    with open(
        pathlib.Path(__file__).parent / "pprof_data/goroutine.out", "rb"
    ) as f:
        return f.read()


@pytest.fixture(scope="session")
def profile10s():
    with open(
        pathlib.Path(__file__).parent / "pprof_data/profile-10seconds.out",
        "rb",
    ) as f:
        return f.read()


@pytest.fixture(scope="session")
def profile10s_profile():
    with open(
        pathlib.Path(__file__).parent / "pprof_data/profile-10seconds.out",
        "rb",
    ) as f:
        return parse_profile(f.read(), "pprof_data/profile-10seconds.out")
