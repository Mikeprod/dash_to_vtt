"""Create a vtt file from a mp4 dash folder.

Author: Mikeprod
Usage: python src/create_vtt_subs.py -i "dash/folder" -o "subs/subtitle.vtt"
"""

import warnings
from logging import getLogger
from pathlib import Path

import click

from src.mp4 import Mp4
from src.vtt import vtt_from_mp4
from src.utils import order_alphabetically
from src.vtt import VTT_HEADER, deduplicate_subtitles

LOGGER = getLogger(__name__)


@click.command()
@click.option(
    "--input", "-i", help="Input MP4 Dash folder. Defaults to 'dash' folder.", default="dash", metavar="FOLDER"
)
@click.option(
    "--output",
    "-o",
    prompt="Output name",
    help="Output vtt file",
    metavar="FILE",
)
@click.help_option("--help", "-h")
def create_vtt(input: str, output: str):
    output_path = Path(output)
    if not output_path.suffix:
        output_path = Path(f"{output}.vtt")
    if output_path.suffix != ".vtt":
        warnings.warn("The extension is not vtt, the created file might not be properly read.")

    input_path = Path(input)
    click.echo(f"Extracting {output_path.absolute()} from the '{input_path.absolute()}' folder")
    extract_vtt_from_dash(input_path, output_path)


def extract_vtt_from_dash(_input: Path, output: Path) -> None:
    """Create a vtt file from a mp4 dash folder.

    :param _input: The mp4 dash folder.
    :type _input: Path
    :param output: The output VTT file
    :type output: Path
    :return: None
    """
    vtt_content = VTT_HEADER
    for _, file in enumerate(order_alphabetically(map(lambda x: x.name, _input.iterdir()))):
        LOGGER.info(file)
        vtt_content += vtt_from_mp4(Mp4(_input / file, load=True))

    txt = deduplicate_subtitles(vtt_content)

    with output.open("wb") as writer:
        writer.write(txt.encode("utf-8"))


if __name__ == "__main__":
    create_vtt()
