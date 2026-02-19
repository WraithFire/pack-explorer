#!/usr/bin/env python3
"""
Manage entries in a pack file (add/remove).

Usage:
    Add:
        # To end of standalone .bin file
        python scripts/manage_entry.py add effect.bin newfile.wan

        # To specific index in standalone .bin file
        python scripts/manage_entry.py add effect.bin newfile.wan -i 42

        # To end of ROM pack (overwrites ROM)
        python scripts/manage_entry.py add game.nds newfile.wan --pack EFFECT/effect.bin

        # To specific index in ROM pack (write to separate file)
        python scripts/manage_entry.py add game.nds newfile.wan -i 42 -o modified.nds --pack EFFECT/effect.bin

    Remove:
        # From standalone .bin file
        python scripts/manage_entry.py remove effect.bin 42

        # From ROM pack (overwrites ROM)
        python scripts/manage_entry.py remove game.nds 42 --pack EFFECT/effect.bin

        # From ROM pack (write to separate file)
        python scripts/manage_entry.py remove game.nds 42 -o modified.nds --pack EFFECT/effect.bin
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from pmd_pack import PackManager, KNOWN_PACK_FILES


def add_file(
    pack_file: Path,
    input_path: Path,
    index: Optional[int] = None,
    output_path: Optional[Path] = None,
    pack_path: str = "EFFECT/effect.bin",
) -> int:
    if output_path is None:
        output_path = pack_file

    manager = PackManager()
    manager.load(pack_file, pack_path)

    idx = manager.add_entry(input_path, index)
    manager.save_as(output_path)
    print(f"Added {input_path.name} at index {idx:04d}, saved to {output_path.name}")

    return idx


def remove_file(
    pack_file: Path,
    index: int,
    output_path: Optional[Path] = None,
    pack_path: str = "EFFECT/effect.bin",
) -> None:
    if output_path is None:
        output_path = pack_file

    manager = PackManager()
    manager.load(pack_file, pack_path)

    if index < 0 or index >= len(manager):
        raise ValueError(f"Index {index} out of range (0-{len(manager)-1})")

    manager.remove_entry(index)
    manager.save_as(output_path)
    print(f"Removed entry {index:04d}, saved to {output_path.name}")


def main():
    parser = argparse.ArgumentParser(description="Manage entries in a pack file.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a file to the pack")
    add_parser.add_argument("pack_file", help="Pack file (.nds ROM or .bin)")
    add_parser.add_argument("input", help="File to add")
    add_parser.add_argument(
        "--index", "-i", type=int, help="Index to insert at (default: end)"
    )
    add_parser.add_argument(
        "--pack",
        default="EFFECT/effect.bin",
        choices=KNOWN_PACK_FILES,
        help="Pack file path in ROM",
    )
    add_parser.add_argument(
        "--output", "-o", help="Output file (defaults to overwriting input pack)"
    )

    remove_parser = subparsers.add_parser(
        "remove", help="Remove an entry from the pack"
    )
    remove_parser.add_argument("pack_file", help="Pack file (.nds ROM or .bin)")
    remove_parser.add_argument("index", type=int, help="Index of entry to remove")
    remove_parser.add_argument(
        "--pack",
        default="EFFECT/effect.bin",
        choices=KNOWN_PACK_FILES,
        help="Pack file path in ROM",
    )
    remove_parser.add_argument(
        "--output", "-o", help="Output file (defaults to overwriting input pack)"
    )

    args = parser.parse_args()

    pack_file = Path(args.pack_file)
    if not pack_file.exists():
        print(f"Error: Pack file not found: {pack_file}")
        sys.exit(1)

    output_path = Path(args.output) if args.output else None

    try:
        if args.command == "add":
            input_path = Path(args.input)
            if not input_path.exists():
                print(f"Error: Input file not found: {input_path}")
                sys.exit(1)
            add_file(pack_file, input_path, args.index, output_path, args.pack)

        elif args.command == "remove":
            remove_file(pack_file, args.index, output_path, args.pack)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
