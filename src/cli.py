import logging
from logging import basicConfig

import click

from src.download import download
from src.create_vtt_subs import create_vtt


@click.group()
@click.option("-v", is_flag=True, help="Verbose")
@click.option("-vv", is_flag=True, help="Extra verbose")
def commands(v: bool, vv: bool) -> None:
    if v:
        basicConfig(level=logging.INFO)
    elif vv:
        basicConfig(level=logging.DEBUG)


def main() -> None:
    """CLI entrypoint."""
    commands.add_command(download)
    commands.add_command(create_vtt)
    commands()


if __name__ == "__main__":
    main()
