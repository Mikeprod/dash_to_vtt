from re import findall
from typing import Any

from src.mp4 import Mp4
from utils import get_int, timedelta_new

VTT_HEADER = "WEBVTT\n"


def extract_text(text: bytes) -> str:
    if text[:4] == b"vtte":
        return ""
    else:
        payload_tag = text.index(b"payl")
        payload_size = get_int(text[payload_tag - 4 : payload_tag])
        cursor = payload_tag + 4
        payload = text[cursor : cursor + payload_size]
        if payload[-4:] == b"vsid":
            payload = payload[:-8]
        payload_cpy = bytes(reversed(payload))
        closing = 0
        try:
            closing = payload_cpy.index(b"\x3e")
        except ValueError:
            pass

        if closing > 0:
            return payload[:-closing].decode("utf-8")
        else:
            return payload.decode("utf-8")


def deduplicate_subtitles(subtitles: str) -> str:
    subs = subtitles.split(" --> ")
    subtitle_entries = []
    for i in range(1, len(subs)):
        start_date = findall(r"\d+:\d+:\d+.\d+", subs[i - 1])  # handle days ?!
        end_date = findall(r"\d+:\d+:\d+.\d+", subs[i])  # handle days ?!
        try:
            start_text = subs[i].index(f"{end_date[0]}\n") + len(f"{end_date[0]}\n")
            if len(end_date) == 2:
                text = subs[i][start_text : subs[i].index(f"\n\n{end_date[1]}")]
            else:
                text = subs[i][start_text:]

        except ValueError:
            print("Split issue in deduplication")
        subtitle_entries.append((start_date[0] if len(start_date) == 1 else start_date[1], end_date[0], text))

    cleaned_entries = []
    for i in range(1, len(subtitle_entries)):
        cleaned_entries.append(subtitle_entries[i - 1])
        if subtitle_entries[i - 1][-1] == subtitle_entries[i][-1]:
            cleaned_entries.remove(subtitle_entries[i - 1])

    subtitles_text = VTT_HEADER
    for start, end, text in cleaned_entries:
        subtitles_text += f"\n{start} --> {end}\n{text}\n"
    return subtitles_text


def generate_timeline(samples: list[dict[str, Any]], time_in_stream: int) -> list[str]:
    timeline = []
    current_time = time_in_stream
    for sample in samples:
        start = str(timedelta_new(milliseconds=current_time))
        end = str(timedelta_new(milliseconds=(current_time := current_time + sample["sample_duration"])))
        timeline.append(f"{start} --> {end}")
    return timeline


def vtt_from_mp4(mp4: Mp4) -> str:
    subs = [extract_text(text) for text in mp4.blocks["mdat"]["samples_content"]]
    timeline = generate_timeline(mp4.blocks["moof"]["traf"]["trun"]["samples"], mp4.blocks["sidx"]["time_in_stream"])
    subtitles = ""
    for i in range(len(subs)):
        if subs[i] != "":
            subtitles += f"\n{timeline[i]}\n{subs[i]}\n"
    return subtitles
