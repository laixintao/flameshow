import os
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from flameshow.main import ensure_tty, main


def test_print_version():
    runner = CliRunner()
    with patch("flameshow.main.__version__", "1.2.3"):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert result.output == "1.2.3\n"


@patch("flameshow.main.os")
def test_run_app(mock_os, data_dir):
    mock_os.isatty.return_value = True
    runner = CliRunner()
    result = runner.invoke(
        main, [str(data_dir / "profile-10seconds.out")], input="q"
    )

    assert result.exit_code == 0


@patch("flameshow.main.sys")
@patch("flameshow.main.os")
def test_ensure_tty_when_its_not(mock_os, mock_sys):
    mock_os.isatty.return_value = False
    opened_fd = object()
    mock_os.fdopen.return_value = opened_fd

    fake_stdin = MagicMock()
    mock_sys.stdin = fake_stdin

    ensure_tty()

    fake_stdin.close.assert_called()
    assert hasattr(mock_sys, "stdin")
    assert mock_sys.stdin is opened_fd
