import re
from logging import getLogger
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from tqdm import tqdm

LOGGER = getLogger(__name__)
# Paste your dash stream url here
STREAM = ""


def is_url_available(url: str) -> bool:
    """Check if the url is available.

    :param url: url to check
    :type url: str
    :return: True if the url is available, False otherwise
    :rtype: bool
    """
    try:
        urlopen(url)
        return True
    except URLError:
        return False


def define_segment_range(url: str, segment_step: int) -> tuple[int, int]:
    """Define the range of the segments.

    :param url: url of the dash file
    :type url: str
    :param segment_step: step between each segment
    :type segment_step: int
    :return: tuple of the range of the segments
    :rtype: tuple
    """
    for i in range(0, 1000000000, segment_step):
        if not is_url_available(url.replace("-0.dash", f"-{i}.dash")):
            return 0, i


def download_dashed_vtt(url: str, dl_dir: str, segment_step: int = 10000, segment_size: int = 1000) -> None:
    """Download dash files that represent the vtt subtitles.

    :param url: url of the dash file
    :type url: str
    :param dl_dir: directory to download the dash files
    :type dl_dir: str
    :param segment_step: step between each segment, defaults to 10000
    :type segment_step: int, optional
    :param segment_size: size of the segment, defaults to 1000
    :type segment_size: int, optional
    :return: None
    :rtype: None
    """
    segment_url = re.sub(r"qsm=\d+-", f"qsm={segment_size}-", url)
    destination = Path(dl_dir)
    destination.mkdir(parents=True, exist_ok=True)

    LOGGER.info(f"Downloading segments to {destination.absolute()}")
    LOGGER.info("After evaluating the number of segments, the download will start.")
    for i in tqdm(range(*define_segment_range(segment_url, segment_step), segment_step)):
        with urlopen(segment_url.replace("-0.dash", f"-{i}.dash")) as data:
            with open(f"{dl_dir}/{i:08d}.mp4", "wb") as writer:
                writer.write(data.read())


if __name__ == "__main__":
    download_dashed_vtt(STREAM, "dash", 10000)
