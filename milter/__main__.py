import logging
import os

import click
from purepythonmilter import (
    DEFAULT_LISTENING_TCP_IP,
    DEFAULT_LISTENING_TCP_PORT,
    DiscardMessage,
    PurePythonMilter,
    RcptTo,
)
from redis.asyncio.client import Redis

logger: logging.LoggerAdapter[logging.Logger]  # assigned below

redis = Redis.from_url(os.environ.get("REDIS_URL"), decode_responses=True)


async def on_rcpt_to(cmd: RcptTo) -> None:
    if await redis.sismember("blocked_emails", cmd.address.lower()):
        logger.info(f"Milter blocked email: {cmd.address}")
        return DiscardMessage()


milter = PurePythonMilter(
    name="change_body",
    hook_on_rcpt_to=on_rcpt_to,
)

logger = milter.logger


# Below is just mostly boilerplate for command line parsing.
@click.command(
    context_settings={
        "show_default": True,
        "max_content_width": 200,
        "auto_envvar_prefix": "PUREPYTHONMILTER",
    }
)
@click.option("--bind-host", default=DEFAULT_LISTENING_TCP_IP, show_envvar=True)
@click.option("--bind-port", default=DEFAULT_LISTENING_TCP_PORT, show_envvar=True)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default="INFO",
    show_envvar=True,
)
@click.version_option(package_name="purepythonmilter", message="%(version)s")
@click.option("--newbody", default="foobar", show_envvar=True)
def main(*, bind_host: str, bind_port: int, log_level: str, newbody: str) -> None:
    """
    This Milter replaces the body with the value given in the `--newbody` parameter.
    """
    logging.basicConfig(level=getattr(logging, log_level))
    milter.run_server(host=bind_host, port=bind_port)


if __name__ == "__main__":
    main()
