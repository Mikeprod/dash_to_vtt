"""Abstraction of the MP4 file format.

Author: Mikeprod
"""

import os
from typing import Any, NamedTuple

from src.utils import get_int


class Block(NamedTuple):
    """Block of data in an mp4 file."""

    name: str
    content: bytes
    size: int
    next_block_size: int
    cursor: int


def read_4(content: bytes, cursor: int) -> bytes:
    """Read 4 bytes from the content at the cursor position."""
    return content[cursor : cursor + 4]


def int_4(content: bytes, cursor: int) -> int:
    """Read 4 bytes from the content at the cursor position and return the integer value."""
    return get_int(read_4(content, cursor))


class Mp4:
    """MP4 file class."""

    def __init__(self, path: str, load: bool) -> None:
        """Create an Mp4 object.

        :param path: path to the mp4 file
        :type path: str
        :param load:  whether to load the file content in memory at creation
        :type load: bool
        :return: None
        """
        if not os.path.isfile(path):
            raise FileNotFoundError(f"File {path} not found")
        self.path = os.path.abspath(path)
        self.content = None
        self._blocks_for_analysis = {}
        if load:
            self._analyse_blocks()

    def load(self) -> None:
        """Load the file content in memory."""
        with open(self.path, "rb") as f:
            self.content = f.read()

    def _analyse_blocks(self) -> None:
        self.blocks = self.read_blocks()
        self.blocks["sidx"] = self.sidx_content()
        if "styp" in self.blocks:
            self.blocks["moof"] = self.moof_content()
            self.blocks["mdat"] = self.mdat_content()

    def read_blocks(self, start: int = 0, stop: int = 0) -> dict[str, Any]:
        """Read the file content and return a list of blocks.

        :param start: start cursor position, defaults to 0
        :type start: int, optional
        :param stop: stop cursor position, defaults to 0
        :type stop: int, optional
        :return: dictionalry of blocks
        :rtype: dict[str, Block]
        """
        if not self.content:
            self.load()
            stop = len(self.content)

        blocks = {}
        while start < stop:
            block = self._read_block(start)
            blocks[block.name] = block.content
            self._blocks_for_analysis[block.name] = block
            start = block.cursor
        return blocks

    def _read_block(self, cursor: int = 0) -> Block:
        """Read a block from the file content.

        :param cursor: cursor position, defaults to 0
        :type cursor: int, optional
        :return: block
        :rtype: Block
        """
        until_next_block = int_4(self.content, cursor)
        cursor += 4
        block_size = until_next_block - 4
        content_size = block_size - 4
        block_name = read_4(self.content, cursor).decode("utf-8")
        cursor += 4
        block_content = self.content[cursor : cursor + content_size]
        cursor += content_size
        next_block_size = int_4(self.content, cursor) if read_4(self.content, cursor) != b"" else 0
        return Block(
            name=block_name, content=block_content, size=block_size, next_block_size=next_block_size, cursor=cursor
        )

    def sidx_content(self) -> dict[str, int]:
        """Parse the sidx block and return its content.

        :return: Dictionary of the sidx block content
        """
        block = self._blocks_for_analysis["sidx"]
        cursor = 0
        t0 = get_int(block.content[cursor : cursor + 4])  # or something else not reported ?
        cursor += 4
        ref_id = get_int(block.content[cursor : cursor + 4])
        cursor += 4
        timescale = get_int(block.content[cursor : cursor + 4])
        cursor += 4
        time_in_stream = get_int(block.content[cursor : cursor + 4])
        cursor += 4
        t1 = get_int(block.content[cursor : cursor + 4])
        cursor += 4
        earliest_presentation_time = get_int(block.content[cursor : cursor + 4])
        cursor += 4
        first_offset = get_int(block.content[cursor : cursor + 4])
        cursor += 4
        reserved = get_int(block.content[cursor : cursor + 2])
        cursor += 2
        reference_count = get_int(block.content[cursor : cursor + 2])
        return {
            "t0": t0,
            "ref_id": ref_id,
            "timescale": timescale,
            "time_in_stream": time_in_stream,
            "t1": t1,
            "earliest_presentation_time": earliest_presentation_time,
            "first_offset": first_offset,
            "reserved": reserved,
            "reference_count": reference_count,
            "content": block.content,
        }

    def moof_content(self) -> dict[str, Any]:
        """Parse the moof block and return its content.

        :return: Dictionary of the moof block content
        """
        block = self._blocks_for_analysis["moof"]
        cursor = block.cursor - block.size + 4
        self.read_blocks(cursor, block.cursor)
        return {"mfhd": self.mfhd_content(), "traf": self.traf_content(), "content": block.content}

    def mfhd_content(self) -> dict[str, int]:
        """Parse the mfhd block and return its content.

        :return: Dictionary of the mfhd block content
        """
        mfhd_block = self._blocks_for_analysis["mfhd"]
        return {"sequence_number": get_int(mfhd_block.content), "content": mfhd_block.content}

    def traf_content(self) -> dict[str, int]:
        """Parse the traf block and return its content.

        :return: Dictionary of the traf block content
        """
        block = self._blocks_for_analysis["traf"]
        cursor = block.cursor - block.size + 4
        self.read_blocks(cursor, block.cursor)
        return {
            "tfhd": self.tfhd_content(),
            "tfdt": self.tfdt_content(),
            "trun": self.trun_content(),
            "content": block.content,
        }

    def tfhd_content(self) -> dict[str, int]:
        """Parse the tfhd block and return its content.

        :return: Dictionary of the tfhd block content
        """
        tfhd_block = self._blocks_for_analysis["tfhd"]
        output = {
            "data_source": get_int(tfhd_block.content[0:2]),
            "length": get_int(tfhd_block.content[2:4]),
            "track_id": get_int(tfhd_block.content[4:8]),
            "sample_number": get_int(tfhd_block.content[8:12]),
            "content": tfhd_block.content,
        }
        if tfhd_block.size - 4 > 12:
            if tfhd_block.size - 4 >= 14:
                output["bytes_per_compression"] = (get_int(tfhd_block.content[12:14]),)

            if tfhd_block.size - 4 >= 16:
                output["samples_per_compression"] = get_int(tfhd_block.content[14:16])
        return output

    def tfdt_content(self) -> dict[str, int]:
        """Parse the tfdt block and return its content.

        :return: Dictionary of the tfdt block content
        """
        tfdt_block = self._blocks_for_analysis["tfdt"]
        version = get_int(tfdt_block.content[:1])
        base_media_decode_time = get_int(tfdt_block.content[1:])
        return {"version": version, "base_media_decode_time": base_media_decode_time, "content": tfdt_block.content}

    def trun_content(self) -> dict[str, int]:
        """Parse the trun block and return its content.

        :return: Dictionary of the trun block content
        """
        trun_block = self._blocks_for_analysis["trun"]
        flags = trun_block.content[:4]  # to be discovered later
        cursor = 4
        samples_count = get_int(trun_block.content[cursor : cursor + 4])
        cursor += 4
        data_offset = get_int(trun_block.content[cursor : cursor + 4])
        cursor += 4
        samples = []
        for _ in range((len(trun_block.content) - cursor) // 8):
            samples.append(
                {
                    "sample_duration": get_int(trun_block.content[cursor : cursor + 4]),
                    "sample_flag": trun_block.content[cursor + 4 : cursor + 8],
                }
            )
            cursor += 8
        return {
            "flags": flags,
            "samples": samples,
            "samples_count": samples_count,
            "data_offset": data_offset,
            "content": trun_block.content,
        }

    def mdat_content(self):
        """Parse the mdat block and return its content.

        :return: Dictionary of the mdat block content
        """
        block = self._blocks_for_analysis["mdat"]
        samples = self.blocks["moof"]["traf"]["trun"]["samples"]
        cursor = 0
        samples_content = []
        for sample in samples:
            content_start = block.content.index(sample["sample_flag"], cursor) + 4
            cursor = content_start + get_int(sample["sample_flag"]) - 4
            samples_content.append(block.content[content_start:cursor])

        return {"content": block.content, "samples_content": samples_content}
