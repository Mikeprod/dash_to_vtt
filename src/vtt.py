from logging import getLogger
from re import findall
from typing import Any

from src.mp4 import Mp4
from src.utils import get_int, timedelta_new

LOGGER = getLogger(__name__)
VTT_HEADER = "WEBVTT\n"


def extract_text(text: bytes) -> dict[str, str]:
    """Extract the text from the mp4 subtitles.

    It also extracts the style for the subtitles as well

    :param text: text to extract
    :type text: bytes
    :return: extracted text and style
    :rtype: dict
    """
    if text[:4] == b"vtte":
        return {"text": "", "style": ""}
    else:
        if text[:4] == b"vttc":
            return parse_vtt_cue(text)
        raise ValueError("Unexpected value in the subtitle")


def parse_vtt_cue(cue: bytes) -> dict[str, str]:
    """Parse the content that starts with vttc.

    vttc stands for VTT Cue.

    :param cue: The content retrieved from the mp4 data
    :type cue: bytes
    :return: the text and style of the VTT Cue

    """
    header_start = 8
    cue_header_size = get_int(cue[4:header_start])
    decoded_style = cue[header_start : header_start + cue_header_size - 4].decode("utf-8").replace("sttg", "")

    payload_tag = cue.index(b"payl")
    payload_size = get_int(cue[payload_tag - 4 : payload_tag])
    cursor = payload_tag + 4
    payload = cue[cursor : cursor + payload_size]
    if payload[-4:] == b"vsid":
        payload = payload[:-8]
    payload_cpy = bytes(reversed(payload))
    closing = 0
    try:
        closing = payload_cpy.index(b"\x3e")
    except ValueError:
        pass
    if closing > 0:
        return {"text": payload[:-closing].decode("utf-8"), "style": decoded_style}
    else:
        return {"text": payload.decode("utf-8"), "style": decoded_style}


def deduplicate_subtitles(subtitles: str) -> str:
    """Deduplicate the subtitles.

    :param subtitles: subtitles to deduplicate
    :type subtitles: str
    :return: deduplicated subtitles
    :rtype: str
    """
    subs = subtitles.split(" --> ")
    subtitle_entries = []
    for i in range(1, len(subs)):
        start_date = findall(r"\d+:\d+:\d+.\d+", subs[i - 1])  # handle days ?!
        end_date = findall(r"\d+:\d+:\d+.\d+", subs[i])  # handle days ?!
        text = ""
        try:
            start_text = subs[i].index(f"{end_date[0]}") + len(f"{end_date[0]}")
            if len(end_date) == 2:
                text = subs[i][start_text : subs[i].index(f"\n\n{end_date[1]}")]
            else:
                text = subs[i][start_text:]

        except ValueError:
            LOGGER.error("Split issue in deduplication")
        subtitle_entries.append((start_date[0] if len(start_date) == 1 else start_date[1], end_date[0], text))

    cleaned_entries = []
    for i in range(1, len(subtitle_entries)):
        cleaned_entries.append(subtitle_entries[i - 1])
        if subtitle_entries[i - 1][-1] == subtitle_entries[i][-1]:
            cleaned_entries.remove(subtitle_entries[i - 1])

    subtitles_text = VTT_HEADER
    for start, end, text in cleaned_entries:
        subtitles_text += f"\n{start} --> {end}{text}\n"
    return subtitles_text


def generate_timeline(samples: list[dict[str, Any]], time_in_stream: int) -> list[str]:
    """Generate the timeline for the subtitles.

    :param samples: Every element of the subtitle timeline
    :type samples: list[dict[str, Any]]
    :param time_in_stream: time in the stream
    :type time_in_stream: int
    :return: The timeline, a list of start and end times
    :rtype: list[str]
    """
    timeline = []
    current_time = time_in_stream
    for sample in samples:
        start = str(timedelta_new(milliseconds=current_time))
        end = str(timedelta_new(milliseconds=(current_time := current_time + sample["sample_duration"])))
        timeline.append(f"{start} --> {end}")
    return timeline


def vtt_from_mp4(mp4: Mp4) -> str:
    """Extract the subtitles from a Dash file.

    :param mp4: Dash file to extract the subtitles from
    :type mp4: Mp4
    :return: The content of the subtitle file
    :rtype: str
    """
    subs = [extract_text(text) for text in mp4.blocks["mdat"]["samples_content"]]
    timeline = generate_timeline(mp4.blocks["moof"]["traf"]["trun"]["samples"], mp4.blocks["sidx"]["time_in_stream"])
    subtitles = ""
    for i in range(len(subs)):
        if subs[i] != "":
            subtitles += f"\n{timeline[i]} {subs[i]['style']}\n{subs[i]['text']}\n"
    return subtitles
