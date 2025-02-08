"""Create a vtt file from a mp4 dash folder.

Author: Mikeprod
Usage: python src/create-vtt-subs.py -i "dash/folder" -o "subs/subtitle.vtt"
"""

from argparse import ArgumentParser, Namespace
from logging import getLogger
from os import listdir

from src.mp4 import Mp4
from src.utils import order_alphabetically
from src.vtt import VTT_HEADER, deduplicate_subtitles, vtt_from_mp4

logger = getLogger(__name__)


def main(arguments: Namespace) -> None:
    """Create a vtt file from a mp4 dash folder.

    :param arguments: Arguments passed to the script (input and output)
    :type arguments: Namespace
    :return: None
    """
    vtt_content = VTT_HEADER
    for _, file in enumerate(order_alphabetically(listdir(arguments.input))):
        logger.info(file)
        vtt_content += vtt_from_mp4(Mp4(f"{arguments.input}\\{file}", load=True))

    txt = deduplicate_subtitles(vtt_content)

    with open(arguments.output, "wb") as writer:
        writer.write(txt.encode("utf-8"))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-i", "--input", dest="input", help="Input mp4 dash folder", metavar="FOLDER", required=True)
    parser.add_argument("-o", "--output", dest="output", help="Output vtt file", metavar="FILE", required=True)
    main(parser.parse_args())
