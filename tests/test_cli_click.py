from click.testing import CliRunner
from flameshow.main import main
from unittest.mock import patch


def test_print_version():
    runner = CliRunner()
    with patch("flameshow.main.__version__", "1.2.3"):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert result.output == "1.2.3\n"


def test_run_app():
    runner = CliRunner()
    result = runner.invoke(
        main, ["tests/pprof_data/profile-10seconds.out"], input="q"
    )

    assert result.exit_code == 0
