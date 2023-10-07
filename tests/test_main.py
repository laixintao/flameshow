import logging
from flameshow.main import setup_log
import os

from unittest.mock import patch


def test_run_app_with_verbose_logging(data_dir):
    # cleanup logfile first
    path = data_dir / "._pytest_flameshow.log"
    try:
        os.remove(path)
    except:  # noqa
        pass

    with patch.object(logging, "basicConfig") as mock_config:
        setup_log(True, logging.DEBUG, path)

        mock_config.assert_called_once()
