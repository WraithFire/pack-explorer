#!/usr/bin/env python3
"""
Verifies that export/import cycles produce identical output:
    - Pack round-trip: export all entries, rebuild pack, compare checksums.
    - Entry round-trip: export/import each entry individually, compare checksums.
    - Manage entry round-trip: add then remove an entry, compare checksums.

Usage:
    python tests/test_roundtrip.py
"""

import hashlib
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from pack_io import export_pack, create_pack
from entry_io import export_entry, import_entry
from manage_entry import add_file, remove_file
from pmd_pack import PackManager

TEST_PACK = Path(__file__).parent / "demo.bin"


def test_pack_roundtrip(pack_file: Path, work_dir: Path) -> bool:
    export_dir = work_dir / "exported"
    rebuilt_pack = work_dir / "rebuilt.bin"

    export_dir.mkdir(exist_ok=True)

    original_checksum = hashlib.md5(pack_file.read_bytes()).hexdigest()

    export_pack(pack_file, export_dir)

    create_pack(export_dir, rebuilt_pack)

    rebuilt_checksum = hashlib.md5(rebuilt_pack.read_bytes()).hexdigest()

    return original_checksum == rebuilt_checksum


def test_entry_roundtrip(pack_file: Path, work_dir: Path) -> tuple:
    manager = PackManager()
    manager.load_from_file(pack_file)
    entry_count = len(manager)

    passed = 0
    failed = 0

    for idx in range(entry_count):
        entry_file = work_dir / f"entry_{idx:04d}.bin"
        modified_pack = work_dir / f"modified_{idx:04d}.bin"

        shutil.copy(pack_file, modified_pack)

        export_entry(pack_file, idx, entry_file)

        import_entry(modified_pack, idx, entry_file, modified_pack)

        original_checksum = hashlib.md5(pack_file.read_bytes()).hexdigest()
        modified_checksum = hashlib.md5(modified_pack.read_bytes()).hexdigest()

        if original_checksum == modified_checksum:
            passed += 1
        else:
            print(f"  ✗ Entry {idx:04d} mismatch")
            failed += 1

        entry_file.unlink()
        modified_pack.unlink()

    return passed, failed


def test_manage_entry_roundtrip(pack_file: Path, work_dir: Path) -> bool:
    modified_pack = work_dir / "modified.bin"
    entry_file = work_dir / "entry_0000.bin"

    shutil.copy(pack_file, modified_pack)

    original_checksum = hashlib.md5(pack_file.read_bytes()).hexdigest()

    # Export entry 0 to use as test data
    export_entry(pack_file, 0, entry_file)

    # Add entry to end of pack
    manager = PackManager()
    manager.load_from_file(modified_pack)
    original_count = len(manager)

    add_file(modified_pack, entry_file, output_path=modified_pack)

    # Verify entry count increased
    manager = PackManager()
    manager.load_from_file(modified_pack)
    if len(manager) != original_count + 1:
        print(f"  ✗ Expected {original_count + 1} entries, got {len(manager)}")
        return False

    # Remove the added entry
    remove_file(modified_pack, original_count, output_path=modified_pack)

    # Verify pack matches original
    modified_checksum = hashlib.md5(modified_pack.read_bytes()).hexdigest()

    return original_checksum == modified_checksum


def main():
    if not TEST_PACK.exists():
        print(f"Error: Test pack not found: {TEST_PACK}")
        sys.exit(1)

    all_passed = True

    print("=== Pack Round-Trip Test ===\n")

    with tempfile.TemporaryDirectory() as tmp:
        result = test_pack_roundtrip(TEST_PACK, Path(tmp))
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}  {TEST_PACK.name}")
        if not result:
            all_passed = False

    print("\n=== Entry Round-Trip Test ===\n")

    with tempfile.TemporaryDirectory() as tmp:
        passed, failed = test_entry_roundtrip(TEST_PACK, Path(tmp))
        print(f"\n{passed} passed, {failed} failed")
        if failed > 0:
            all_passed = False

    print("\n=== Manage Entry Round-Trip Test ===\n")

    with tempfile.TemporaryDirectory() as tmp:
        result = test_manage_entry_roundtrip(TEST_PACK, Path(tmp))
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}  add + remove")
        if not result:
            all_passed = False

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
