import logging
import os
import time

import sys

import click

from flameshow import __version__
from flameshow.parsers import parse
from flameshow.render import FlameshowApp


logger = logging.getLogger(__name__)


def setup_log(enabled, level, loglocation):
    if enabled:
        logging.basicConfig(
            filename=os.path.expanduser(loglocation),
            filemode="a",
            format=(
                "%(asctime)s %(levelname)5s (%(module)sL%(lineno)d)"
                " %(message)s"
            ),
            level=level,
        )
    else:
        logging.disable(logging.CRITICAL)
    logger.info("------ flameshow ------")


LOG_LEVEL = {
    0: logging.CRITICAL,
    1: logging.WARNING,
    2: logging.INFO,
    3: logging.DEBUG,
}


def ensure_tty():
    if os.isatty(0):
        return

    logger.info("stdin is not a tty, replace it to fd=2")
    sys.stdin.close()
    sys.stdin = os.fdopen(2)


def run_app(verbose, log_to, profile_f, _debug_exit_after_rednder):
    log_level = LOG_LEVEL[verbose]
    setup_log(log_to is not None, log_level, log_to)

    t0 = time.time()
    profile_data = profile_f.read()

    profile = parse(profile_data, profile_f.name)

    t01 = time.time()
    logger.info("Parse profile, took %.3fs", t01 - t0)

    ensure_tty()
    app = FlameshowApp(
        profile,
        _debug_exit_after_rednder,
    )
    app.run()


def print_version(ctx, _, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(__version__)
    ctx.exit()


@click.command()
@click.option(
    "-v",
    "--verbose",
    count=True,
    default=2,
    help="Add log verbose level, using -v, -vv, -vvv for printing more logs.",
)
@click.option(
    "-l",
    "--log-to",
    type=click.Path(),
    default=None,
    help="Printing logs to a file, for debugging, default is no logs.",
)
@click.option(
    "--version",
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
)
@click.argument("profile", type=click.File("rb"))
def main(verbose, log_to, profile):
    run_app(verbose, log_to, profile, _debug_exit_after_rednder=False)


if __name__ == "__main__":
    main()
