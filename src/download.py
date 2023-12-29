import re
import time
from urllib.request import urlopen

# Paste your sash stream url here
stream = ""


def download_dashed_vtt(url: str, dl_dir: str, segment_step: int = 10000, segment_size: int = 1000) -> None:
    """Download dash files that represent the vtt subtitles.

    :param url: url of the dash file
    :type url: str
    :param segment_step: step between each segment, defaults to 10000
    :type segment_step: int, optional
    :param segment_size: size of the segment, defaults to 1000
    :type segment_size: int, optional
    :return: None
    :rtype: None
    """
    segment_url = re.sub(r"qsm=\d+-", f"qsm={segment_size}-", url)
    for i in range(0, 1000000000, segment_step):
        with urlopen(
                segment_url.replace("-0.dash", f"-{i}.dash")
        ) as data:
            with open(f"{dl_dir}/{i:08d}.mp4", "wb") as writer:
                writer.write(data.read())
        time.sleep(0.5)


if __name__ == '__main__':
    download_dashed_vtt(stream, "dash", 10000)
