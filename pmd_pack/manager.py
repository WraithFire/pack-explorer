"""
Pack file manager - Logic for pack file operations.
"""

import hashlib
from pathlib import Path
from typing import Optional, Set, Tuple
from .model import PackFile
from .file_types import detect_type, type_to_ext
from .pkdpx import Pkdpx


KNOWN_PACK_FILES = [
    "EFFECT/effect.bin",
    "DUNGEON/dungeon.bin",
    "MONSTER/monster.bin",
    "MONSTER/m_attack.bin",
    "MONSTER/m_ground.bin",
    "BALANCE/m_level.bin",
]


class PackManager:

    def __init__(self):
        self.pack: Optional[PackFile] = None
        self.rom = None  # NintendoDSRom
        self.pack_path: str = KNOWN_PACK_FILES[0]
        self.file_path: Optional[Path] = None
        self.modified: bool = False
        self.modified_indices: Set[int] = set()
        self._loaded_data: Optional[bytes] = None
        # Checksum caching
        self._loaded_checksum: Optional[str] = None
        self._current_checksum: Optional[str] = None

    def create_new(self) -> None:
        self.pack = PackFile()
        self.rom = None
        self.pack_path = ""
        self.file_path = None
        self.modified = True
        self.modified_indices.clear()
        self._loaded_data = None

    def load_from_file(self, path: Path) -> int:
        data = path.read_bytes()
        self._validate_pack(data)

        self.pack = PackFile(data)
        self.rom = None
        self.pack_path = ""
        self.file_path = path
        self.modified = False
        self.modified_indices.clear()
        self._loaded_data = data
        self._cache_loaded_checksum()
        self._current_checksum = self._loaded_checksum

        return len(self.pack)

    def load_from_rom(self, path: Path, pack_path: str) -> int:
        from ndspy.rom import NintendoDSRom

        self.rom = NintendoDSRom.fromFile(str(path))
        data = self.rom.getFileByName(pack_path)
        self._validate_pack(data)

        self.pack = PackFile(data)
        self.pack_path = pack_path
        self.file_path = path
        self.modified = False
        self.modified_indices.clear()
        self._loaded_data = data
        self._cache_loaded_checksum()
        self._current_checksum = self._loaded_checksum

        return len(self.pack)

    def load(self, path: Path, pack_path: str = KNOWN_PACK_FILES[0]) -> int:
        if path.suffix.lower() == ".nds":
            return self.load_from_rom(path, pack_path)
        return self.load_from_file(path)

    def switch_pack(self, pack_path: str) -> int:
        if not self.rom:
            raise RuntimeError("No ROM loaded")

        data = self.rom.getFileByName(pack_path)
        self._validate_pack(data)

        self.pack = PackFile(data)
        self.pack_path = pack_path
        self.modified = False
        self.modified_indices.clear()
        self._loaded_data = data
        self._cache_loaded_checksum()
        self._current_checksum = self._loaded_checksum

        return len(self.pack)

    def _validate_pack(self, data: bytes):
        if len(data) < 16:
            raise ValueError("File too small")
        if data[0:4] != b"\x00\x00\x00\x00":
            raise ValueError("Invalid header (expected 0x00000000)")
        file_count = int.from_bytes(data[4:8], "little")
        if file_count == 0 or file_count > 10000:
            raise ValueError(f"Unreasonable file count ({file_count})")

    def _ensure_loaded(self):
        if self.pack is None:
            raise RuntimeError("No file loaded")

    def _maybe_compress(self, data: bytes, compress: bool) -> bytes:
        if compress and detect_type(data) != "PKDPX":
            return Pkdpx.compress(data)
        return data

    def _maybe_decompress(self, data: bytes, decompress: bool) -> bytes:
        if decompress and detect_type(data) == "PKDPX":
            return Pkdpx.decompress(data)
        return data

    def save(self) -> None:
        if not self.pack or not self.file_path:
            raise RuntimeError("No file loaded")

        if self.rom:
            self._save_to_rom(self.file_path)
        else:
            self._save_to_file(self.file_path)

    def save_as(self, path: Path, save_rom: bool = None) -> None:
        if self.pack is None:
            raise RuntimeError("No file loaded")

        if save_rom is None:
            save_rom = bool(self.rom and path.suffix.lower() == ".nds")

        if save_rom and self.rom:
            self._save_to_rom(path)
        else:
            self._save_to_file(path)

    def _save_to_file(self, path: Path) -> None:
        data = self.pack.to_bytes()
        path.write_bytes(data)

        if not self.rom:
            self.file_path = path
            self.modified = False
            self.modified_indices.clear()
            self._loaded_data = data
            self._cache_loaded_checksum()
            self._current_checksum = self._loaded_checksum

    def _save_to_rom(self, path: Path) -> None:
        data = self.pack.to_bytes()
        self.rom.setFileByName(self.pack_path, data)
        self.rom.saveToFile(str(path))

        self.file_path = path
        self.modified = False
        self.modified_indices.clear()
        self._loaded_data = data
        self._cache_loaded_checksum()
        self._current_checksum = self._loaded_checksum

    def import_entry(self, idx: int, path: Path) -> str:
        self._ensure_loaded()
        return self.import_data(idx, path.read_bytes())

    def import_data(self, idx: int, data: bytes, compress: bool = False) -> str:
        self._ensure_loaded()
        data = self._maybe_compress(data, compress)
        self.pack[idx] = data
        self.modified = True
        self.modified_indices.add(idx)
        self._invalidate_current_checksum()
        return detect_type(data)

    def add_entry(self, path: Path, idx: Optional[int] = None) -> int:
        self._ensure_loaded()
        return self.add_data(path.read_bytes(), idx)

    def add_data(
        self, data: bytes, idx: Optional[int] = None, compress: bool = False
    ) -> int:
        self._ensure_loaded()
        data = self._maybe_compress(data, compress)

        if idx is None:
            idx = len(self.pack)
            self.pack.append(data)
        else:
            self.pack.insert(idx, data)

        self.modified = True
        self.modified_indices.add(idx)
        self._invalidate_current_checksum()
        return idx

    def remove_entry(self, idx: int):
        self._ensure_loaded()
        del self.pack[idx]
        self.modified = True
        self.modified_indices = {
            i if i < idx else i - 1 for i in self.modified_indices if i != idx
        }
        self._invalidate_current_checksum()

    def get_entry_data(self, idx: int, decompress: bool = False) -> bytes:
        self._ensure_loaded()
        return self._maybe_decompress(self.pack[idx], decompress)

    def get_export_info(self, idx: int, decompress: bool = False) -> tuple:
        self._ensure_loaded()
        data = self._maybe_decompress(self.pack[idx], decompress)
        etype = detect_type(data)
        return data, etype, type_to_ext(etype)

    def export_entry(self, idx: int, path: Path):
        self._ensure_loaded()
        path.write_bytes(self.pack[idx])

    def export_all(self, directory: Path, decompress: bool = False) -> int:
        self._ensure_loaded()
        for i in range(len(self.pack)):
            data, etype, ext = self.get_export_info(i, decompress)
            (directory / f"entry_{i:04d}{ext}").write_bytes(data)
        return len(self.pack)

    def import_all(self, directory: Path, compress: bool = False) -> int:
        self._ensure_loaded()
        files = sorted(f for f in directory.iterdir() if f.is_file())
        if not files:
            return 0

        self.pack.clear()
        for file in files:
            self.pack.append(self._maybe_compress(file.read_bytes(), compress))

        self.modified = True
        self.modified_indices = set(range(len(self.pack)))
        self._invalidate_current_checksum()
        return len(self.pack)

    def get_entry_info(self, idx: int) -> Tuple[str, int]:
        self._ensure_loaded()
        data = self.pack[idx]
        return detect_type(data), len(data)

    def get_loaded_checksum(self) -> str:
        if self._loaded_checksum is None:
            return "-"
        return self._loaded_checksum

    def get_current_checksum(self) -> str:
        if self.pack is None:
            return "-"
        if self._current_checksum is None:
            self._current_checksum = hashlib.md5(self.pack.to_bytes()).hexdigest()
        return self._current_checksum

    def _invalidate_current_checksum(self):
        self._current_checksum = None

    def _cache_loaded_checksum(self):
        if self._loaded_data is not None:
            self._loaded_checksum = hashlib.md5(self._loaded_data).hexdigest()
        else:
            self._loaded_checksum = None

    def get_loaded_size(self) -> int:
        if self._loaded_data is None:
            return 0
        return len(self._loaded_data)

    def get_current_size(self) -> int:
        if self.pack is None:
            return 0
        return self.pack.get_size()

    def __len__(self) -> int:
        if self.pack is None:
            return 0
        return len(self.pack)

    def __iter__(self):
        if self.pack is None:
            return iter([])
        return iter(self.pack)
