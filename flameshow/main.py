import json
import logging
import os
import time
import click
from click.exceptions import UsageError


from flameshow.parser import ProfileParser
from flameshow.render import FlameGraphApp
from flameshow.pprof_parser import parse_golang_profile
from flameshow.const import MAX_RENDER_DEPTH, MIN_RENDER_DEPTH
from flameshow import __version__


logger = logging.getLogger(__name__)


def setup_log(enabled, level, loglocation):
    if enabled:
        logging.basicConfig(
            filename=os.path.expanduser(loglocation),
            filemode="a",
            format="%(asctime)s %(levelname)5s (%(module)s) %(message)s",
            level=level,
        )
    else:
        logging.disable(logging.CRITICAL)
    logger.info("------ flameshow ------")


LOG_LEVEL = {0: logging.CRITICAL, 1: logging.WARNING, 2: logging.INFO, 3: logging.DEBUG}


def run_app(verbose, log_to, format, profile, _debug_exit_after_rednder):
    log_level = LOG_LEVEL[verbose]
    setup_log(log_to is not None, log_level, log_to)

    logger.info(f"run app, {format=}")

    t0 = time.time()
    profile_data = profile.read()
    profile_dict = parse_golang_profile(profile_data)
    t01 = time.time()
    logger.info("Read golang profile, took %.2fs", t01 - t0)

    if format == "json":
        click.echo(json.dumps(profile_dict, indent=2, sort_keys=True))
    elif format == "flamegraph":
        parser_obj = ProfileParser(filename=profile.name)
        t1 = time.time()
        profile = parser_obj.parse(profile_dict)
        logger.info("Max depth: %s", parser_obj.highest)
        t2 = time.time()
        logger.info("parse json files cost %s s", t2 - t1)

        render_depth = MAX_RENDER_DEPTH - int(parser_obj.total_sample / 100)
        # limit to 3 - 10
        render_depth = max(MIN_RENDER_DEPTH, render_depth)
        render_depth = min(MAX_RENDER_DEPTH, render_depth)

        logger.info(
            "Start to render app, total samples=%d, render_depth=%d",
            parser_obj.total_sample,
            render_depth,
        )

        app = FlameGraphApp(
            profile,
            render_depth,
            _debug_exit_after_rednder,
        )
        app.run()

    else:
        raise UsageError("Unsupported format = {}".format(format))


def print_version(ctx, param, value):
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
    "-f",
    "--format",
    type=click.Choice(["flamegraph", "json"], case_sensitive=False),
    default="flamegraph",
)
@click.option(
    "--version", is_flag=True, callback=print_version, expose_value=False, is_eager=True
)
@click.argument("profile", type=click.File("rb"))
def main(verbose, log_to, format, profile):
    run_app(verbose, log_to, format, profile, _debug_exit_after_rednder=False)


if __name__ == "__main__":
    main(True, 3, "lucky.log")
