"""
File type detection utilities for pack file entries.
Based on skytemple_files
"""


def detect_type(data: bytes) -> str:
    if len(data) < 16:
        return "Unknown"

    if data[0:4] == b"SIR0":
        subheader_ptr = int.from_bytes(data[4:8], "little")
        if subheader_ptr + 32 <= len(data):
            pad1 = int.from_bytes(
                data[subheader_ptr + 0x18 : subheader_ptr + 0x1C], "little"
            )
            pad2 = int.from_bytes(
                data[subheader_ptr + 0x1C : subheader_ptr + 0x20], "little"
            )

            if pad1 == 0xAAAAAAAA and pad2 == 0xAAAAAAAA:
                s_img_ptr = int.from_bytes(
                    data[subheader_ptr + 12 : subheader_ptr + 16], "little"
                )
                s_pal_ptr = int.from_bytes(
                    data[subheader_ptr + 16 : subheader_ptr + 20], "little"
                )

                is_screen = False
                if (0 < s_img_ptr < len(data)) and (0 < s_pal_ptr < len(data)):
                    is_screen = True

                if is_screen:
                    return "Screen"

        if subheader_ptr + 10 <= len(data):
            sprite_type = int.from_bytes(
                data[subheader_ptr + 8 : subheader_ptr + 10], "little"
            )
            w_anim_info_ptr = int.from_bytes(
                data[subheader_ptr : subheader_ptr + 4], "little"
            )
            w_img_info_ptr = int.from_bytes(
                data[subheader_ptr + 4 : subheader_ptr + 8], "little"
            )

            if w_anim_info_ptr < len(data) and w_img_info_ptr < len(data):
                if sprite_type == 0 or sprite_type == 1 or sprite_type == 2:
                    return "WAN"
                elif sprite_type == 3:
                    return "WAT"

        if subheader_ptr + 16 <= len(data):
            magic = data[subheader_ptr : subheader_ptr + 5]
            if magic == b"AT4PX":
                return "SIR0(AT4PX)"
            elif magic == b"PKDPX":
                return "SIR0(PKDPX)"
            elif data[subheader_ptr : subheader_ptr + 4] == b"WTE\0":
                return "WTE"

            try:
                first_ptr = int.from_bytes(
                    data[subheader_ptr : subheader_ptr + 4], "little"
                )
                if 0 <= first_ptr < len(data):
                    if first_ptr + 8 <= len(data):
                        nb_colors = int.from_bytes(
                            data[first_ptr : first_ptr + 2], "little"
                        )
                        if 0 < nb_colors <= 256:
                            if first_ptr + 4 + 3 < len(data):
                                if data[first_ptr + 7] == 0x80:
                                    return "SIR0(DPLA)"
                        elif nb_colors == 0:
                            if first_ptr + 3 < len(data):
                                if data[first_ptr + 2] == 0x04:
                                    return "SIR0(DPLA)"
            except Exception:
                pass

            try:
                if subheader_ptr + 4 <= len(data):
                    if data[subheader_ptr + 3] == 0xFF:
                        is_colvec = True
                        for i in range(min(4, (len(data) - subheader_ptr) // 4)):
                            if data[subheader_ptr + i * 4 + 3] != 0xFF:
                                is_colvec = False
                                break
                        if is_colvec:
                            return "SIR0(COLVEC)"
            except Exception:
                pass

            try:
                ptr_tiles = int.from_bytes(
                    data[subheader_ptr : subheader_ptr + 4], "little"
                )
                ptr_pal = int.from_bytes(
                    data[subheader_ptr + 4 : subheader_ptr + 8], "little"
                )
                if 0 < ptr_tiles < len(data) and 0 < ptr_pal < len(data):
                    if ptr_tiles < ptr_pal:
                        if (ptr_pal - ptr_tiles) == 3072:
                            return "SIR0(ZMAPPAT)"
            except Exception:
                pass

            try:
                ptr_spr = int.from_bytes(
                    data[subheader_ptr + 4 : subheader_ptr + 8], "little"
                )
                ptr_pal = int.from_bytes(
                    data[subheader_ptr + 8 : subheader_ptr + 0xC], "little"
                )
                if (0 < ptr_spr < len(data)) and (0 < ptr_pal < len(data)):
                    return "SIR0(IMG)"
            except Exception:
                pass

        return "SIR0"

    # Standalone formats — match by magic bytes
    if len(data) >= 5:
        if data[0:5] == b"AT4PX":
            return "AT4PX"
        if data[0:5] == b"PKDPX":
            return "PKDPX"
        if data[0:4] == b"WTU\0":
            return "WTU"

    # Headerless formats — match by structural heuristics
    if len(data) >= 32:
        val0 = int.from_bytes(data[0:4], "little")
        if val0 == 32:
            pal_len = int.from_bytes(data[4:8], "little")
            if pal_len > 0 and pal_len % 16 == 0:
                return "BGP"

    if len(data) >= 16 and len(data) % 4 == 0:
        is_dpl = True
        limit = min(len(data), 64)
        for i in range(3, limit, 4):
            if data[i] != 0x80:
                is_dpl = False
                break
        if is_dpl:
            return "DPL"

    type_val = int.from_bytes(data[0:4], "little")
    if type_val == 2:
        return "WBA"

    if len(data) in [24576, 1604]:
        return "RAW_4BPP"

    return "Unknown"


def detect_inner_type(data: bytes) -> tuple[str, bytes]:
    from .pkdpx import Pkdpx

    outer_type = detect_type(data)

    if outer_type == "PKDPX":
        try:
            decompressed = Pkdpx.decompress(data)
            inner_type = detect_type(decompressed)
            return f"PKDPX({inner_type})", decompressed
        except Exception:
            return outer_type, data

    return outer_type, data


def type_to_ext(file_type: str) -> str:
    ext_map = {
        "WAN": ".wan",  # Official extension
        "WAT": ".wat",  # Official extension
        "Screen": ".screen",
        "WBA": ".wba",  # Official extension
        "SIR0": ".bin",
        "AT4PX": ".at4px",
        "PKDPX": ".pkdpx",
        "SIR0(AT4PX)": ".at4px",
        "SIR0(PKDPX)": ".pkdpx",
        "WTE": ".wte",  # Official extension
        "WTU": ".wtu",  # Official extension
        "SIR0(DPLA)": ".dpla",
        "SIR0(IMG)": ".img",
        "SIR0(COLVEC)": ".colvec",
        "SIR0(ZMAPPAT)": ".zmappat",
        "BGP": ".bgp",  # Official extension
        "DPL": ".dpl",
        "RAW_4BPP": ".img",
        "Unknown": ".bin",
    }

    if file_type.startswith("PKDPX("):
        return ".pkdpx"

    return ext_map.get(file_type, ".bin")


def format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
