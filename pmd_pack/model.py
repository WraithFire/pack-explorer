"""
Parser and serializer for the .bin pack container format.
Based on skytemple_files.container.pmd_pack

Format:
    Header (8 bytes):
        - 4 bytes: Padding (0x00)
        - 4 bytes: File count (uint32)
    TOC (8 bytes/file + 8 bytes null):
        - 4 bytes: Offset
        - 4 bytes: Length
    Data: 16-byte aligned, 0xFF padded.
"""

from typing import List, Optional, Union

ALIGNMENT = 16
HEADER_SIZE = 8
TOC_ENTRY_SIZE = 8
TOC_TERMINATOR_SIZE = 8


def read_u32(data: Union[bytes, memoryview], offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], "little")


def write_u32(data: bytearray, value: int, offset: int) -> None:
    data[offset : offset + 4] = value.to_bytes(4, "little")


def align_up(value: int, alignment: int = ALIGNMENT) -> int:
    return (value + alignment - 1) & ~(alignment - 1)


class PackFile:
    def __init__(self, data: Optional[bytes] = None):
        self._files: List[bytes] = []
        self._header_len: Optional[int] = None

        if data is not None:
            self._parse(data)

    def _parse(self, data: bytes) -> None:
        view = memoryview(data) if not isinstance(data, memoryview) else data
        num_files = read_u32(view, 4)

        if num_files > 0:
            self._header_len = read_u32(view, HEADER_SIZE)

        for i in range(num_files):
            toc_offset = HEADER_SIZE + i * TOC_ENTRY_SIZE
            file_ptr = read_u32(view, toc_offset)
            file_len = read_u32(view, toc_offset + 4)
            self._files.append(view[file_ptr : file_ptr + file_len].tobytes())

    def _calculate_header_length(self) -> int:
        min_len = align_up(
            HEADER_SIZE + len(self._files) * TOC_ENTRY_SIZE + TOC_TERMINATOR_SIZE
        )
        # Preserve original header length to maintain byte-perfect round-trips
        if self._header_len is not None and self._header_len >= min_len:
            return self._header_len
        return min_len

    def _calculate_total_size(self, header_len: int) -> int:
        return header_len + sum(align_up(len(f)) for f in self._files)

    def validate(self) -> None:
        if len(self._files) == 0:
            raise ValueError("Pack has no files")

        for i, f in enumerate(self._files):
            if not isinstance(f, bytes):
                raise ValueError(f"Entry {i} is not bytes")
            if len(f) == 0:
                raise ValueError(f"Entry {i} is empty")

    def to_bytes(self) -> bytes:
        self.validate()

        header_len = self._calculate_header_length()
        total_size = self._calculate_total_size(header_len)

        out = bytearray(b"\xff" * total_size)

        write_u32(out, 0, 0)
        write_u32(out, len(self._files), 4)

        data_cursor = header_len
        toc_cursor = HEADER_SIZE

        for file_data in self._files:
            write_u32(out, data_cursor, toc_cursor)
            write_u32(out, len(file_data), toc_cursor + 4)
            out[data_cursor : data_cursor + len(file_data)] = file_data

            data_cursor = align_up(data_cursor + len(file_data))
            toc_cursor += TOC_ENTRY_SIZE

        write_u32(out, 0, toc_cursor)
        write_u32(out, 0, toc_cursor + 4)

        return bytes(out)

    def get_size(self) -> int:
        header_len = self._calculate_header_length()
        return self._calculate_total_size(header_len)

    def __len__(self) -> int:
        return len(self._files)

    def __getitem__(self, key: int) -> bytes:
        return self._files[key]

    def __setitem__(self, key: int, value: bytes) -> None:
        self._files[key] = value

    def __delitem__(self, key: int) -> None:
        del self._files[key]

    def __iter__(self):
        return iter(self._files)

    def insert(self, index: int, item: bytes) -> None:
        self._files.insert(index, item)

    def append(self, item: bytes) -> None:
        self._files.append(item)

    def clear(self) -> None:
        self._files.clear()

    def extend(self, items: List[bytes]) -> None:
        self._files.extend(items)
