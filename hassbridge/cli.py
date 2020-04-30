"""hassbridge cli."""
import logging
from dataclasses import dataclass

import asyncclick as click

from hassbridge.hassinterface import HassInterface

click.anyio_backend = "asyncio"


@dataclass
class Settings:
    """Settings container."""

    endpoint: str
    token: str
    debug: bool = False


@click.group(invoke_without_command=True)
@click.option("--endpoint", required=False, envvar="HASSBRIDGE_ENDPOINT")
@click.option("--token", required=False, envvar="HASSBRIDGE_TOKEN")
@click.option("-d", "--debug", is_flag=True)
@click.pass_context
async def cli(ctx, endpoint, token, debug):
    """hass-mpris bridge."""
    ctx.obj = Settings(endpoint=endpoint, token=token, debug=debug)

    if ctx.invoked_subcommand is None:
        await ctx.invoke(start)


@cli.command()
@click.pass_context
async def start(ctx):
    """Start bridging homeassistant to mpris."""
    settings: Settings = ctx.obj

    lvl = logging.INFO
    if settings.debug:
        lvl = logging.DEBUG
        if settings.debug < 2:
            # websockets.protocol is very verbose otherwise...
            logging.getLogger("websockets.protocol").setLevel(logging.INFO)

    logging.basicConfig(level=lvl)
    # TODO: something initializes logger before we get here,
    # so we need to set the level for default logger separately
    # to get any logging below WARNNING
    # this can be removed after that's fixed.
    logging.getLogger().setLevel(lvl)

    logging.info("Endpoint: %s" % settings.endpoint)

    h = HassInterface(settings.endpoint, settings.token)

    await h.start()


if __name__ == "__main__":
    cli(_anyio_backend="asyncio")
