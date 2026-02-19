#!/usr/bin/env python3
"""
Export or import entire pack files.

Usage:
    Export:
        # From standalone .bin file
        python scripts/pack_io.py export effect.bin output_dir/

        # From ROM (specify pack path)
        python scripts/pack_io.py export game.nds output_dir/ --pack EFFECT/effect.bin

    Import:
        # Create standalone .bin file from directory
        python scripts/pack_io.py import entries_dir/ output.bin

        # Inject into ROM (overwrites source ROM)
        python scripts/pack_io.py import entries_dir/ game.nds --pack EFFECT/effect.bin

        # Inject into ROM (write to separate file)
        python scripts/pack_io.py import entries_dir/ modified.nds -s original.nds --pack EFFECT/effect.bin
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from pmd_pack import PackManager, KNOWN_PACK_FILES


def export_pack(
    input_path: Path,
    output_dir: Path,
    pack_path: str = "EFFECT/effect.bin",
) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)

    manager = PackManager()
    manager.load(input_path, pack_path)

    exported = manager.export_all(output_dir)
    print(f"Exported {exported} entries to {output_dir}/")

    return exported


def create_pack(
    input_dir: Path,
    output_file: Path,
    pack_path: Optional[str] = None,
    source_rom: Optional[Path] = None,
) -> int:
    manager = PackManager()

    if output_file.suffix.lower() == ".nds":
        if source_rom is None:
            raise ValueError("Source ROM required for .nds output")
        if pack_path is None:
            raise ValueError("Pack path required for .nds output")

        # Load existing pack to preserve header
        manager.load(source_rom, pack_path)
        count = manager.import_all(input_dir)

        if count == 0:
            print("Warning: No files found in directory")
            return 0

        from ndspy.rom import NintendoDSRom

        rom = NintendoDSRom.fromFile(str(source_rom))
        rom.setFileByName(pack_path, manager.pack.to_bytes())
        rom.saveToFile(str(output_file))
        print(f"Injected {count} entries into {output_file.name} ({pack_path})")
    else:
        # Creating new standalone file - no header to preserve
        manager.create_new()
        count = manager.import_all(input_dir)

        if count == 0:
            print("Warning: No files found in directory")
            return 0

        manager.save_as(output_file)
        print(f"Created {output_file.name} with {count} entries")

    return count


def main():
    parser = argparse.ArgumentParser(description="Export or import entire pack files.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser(
        "export", help="Export all entries to directory"
    )
    export_parser.add_argument("input", help="Input file (.nds ROM or .bin pack file)")
    export_parser.add_argument("output", help="Output directory")
    export_parser.add_argument(
        "--pack",
        default="EFFECT/effect.bin",
        choices=KNOWN_PACK_FILES,
        help="Pack file path in ROM (only for .nds input)",
    )

    import_parser = subparsers.add_parser("import", help="Create pack from directory")
    import_parser.add_argument("input_dir", help="Input directory with files to pack")
    import_parser.add_argument("output_file", help="Output file (.bin or .nds)")
    import_parser.add_argument(
        "--pack",
        default="EFFECT/effect.bin",
        choices=KNOWN_PACK_FILES,
        help="Pack path in ROM (required for .nds output)",
    )
    import_parser.add_argument(
        "--source",
        "-s",
        help="Source ROM to copy (required for .nds output, defaults to output file if it exists)",
    )

    args = parser.parse_args()

    try:
        if args.command == "export":
            input_path = Path(args.input)
            output_dir = Path(args.output)

            if not input_path.exists():
                print(f"Error: Input file not found: {input_path}")
                sys.exit(1)

            export_pack(input_path, output_dir, args.pack)

        elif args.command == "import":
            input_dir = Path(args.input_dir)
            output_file = Path(args.output_file)

            if not input_dir.exists():
                print(f"Error: Input directory not found: {input_dir}")
                sys.exit(1)

            source_rom = None
            pack_path = None
            if output_file.suffix.lower() == ".nds":
                pack_path = args.pack
                if args.source:
                    source_rom = Path(args.source)
                elif output_file.exists():
                    source_rom = output_file
                else:
                    print("Error: Source ROM required for .nds output (use --source)")
                    sys.exit(1)

                if not source_rom.exists():
                    print(f"Error: Source ROM not found: {source_rom}")
                    sys.exit(1)

            create_pack(input_dir, output_file, pack_path, source_rom)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
