import struct
from pathlib import Path

from util import options

from segtypes.gc.segment import GCSegment


class GcSegBootinfo(GCSegment):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def split(self, iso_bytes):
        lines = []

        gc_dvd_magic = struct.unpack_from(">I", iso_bytes, 0x1C)[0]
        assert gc_dvd_magic == 0xC2339F3D

        # Gathering variables
        system_code = chr(iso_bytes[0x00])
        game_code = iso_bytes[0x01:0x03].decode("utf-8")
        region_code = chr(iso_bytes[0x03])
        publisher_code = iso_bytes[0x04:0x06].decode("utf-8")

        disc_id = iso_bytes[0x06]
        game_version = iso_bytes[0x07]
        audio_streaming = iso_bytes[0x08]
        stream_buffer_size = iso_bytes[0x09]

        name = iso_bytes[0x20:0x400].decode("utf-8").strip("\x00")
        name_padding_len = 0x3E0 - len(name)

        # The following is from YAGCD, don't know what they were for:
        # https://web.archive.org/web/20220528011846/http://hitmen.c02.at/files/yagcd/yagcd/chap13.html#sec13.1
        apploader_size = struct.unpack_from(">I", iso_bytes, 0x400)[0]
        debug_monitor_address = struct.unpack_from(">I", iso_bytes, 0x404)[0]

        # These on the other hand are easy to understand
        dol_offset = struct.unpack_from(">I", iso_bytes, 0x420)[0]
        fst_offset = struct.unpack_from(">I", iso_bytes, 0x424)[0]
        fst_size = struct.unpack_from(">I", iso_bytes, 0x428)[0]
        fst_max_size = struct.unpack_from(">I", iso_bytes, 0x42C)[0]

        user_position = struct.unpack_from(">I", iso_bytes, 0x430)[0]
        user_length = struct.unpack_from(">I", iso_bytes, 0x434)[0]
        unk_int = struct.unpack_from(">I", iso_bytes, 0x438)[0]

        # Outputting .s file
        lines.append(f"# GameCube disc image boot data, located at 0x00 in the disc.\n")
        lines.append(f"# Generated by splat.\n\n")

        lines.append(f".section .data\n\n")

        # Game ID stuff
        lines.append(f'system_code: .ascii "{system_code}"\n')
        lines.append(f'game_code: .ascii "{game_code}"\n')
        lines.append(f'region_code: .ascii "{region_code}"\n')
        lines.append(f'publisher_code: .ascii "{publisher_code}"\n\n')

        lines.append(f"disc_id: .byte {disc_id:X}\n")
        lines.append(f"game_version: .byte {game_version:X}\n")
        lines.append(f"audio_streaming: .byte {audio_streaming:X}\n")
        lines.append(f"stream_buffer_size: .byte {stream_buffer_size:X}\n\n")

        # padding
        lines.append(f".fill 0x12\n\n")

        # GC magic number
        lines.append(f"gc_magic: .long 0xC2339F3D\n\n")

        # Long game name
        lines.append(f'game_name: .ascii "{name}"\n')
        lines.append(f".org 0x400\n\n")

        lines.append(f"apploader_size: .long 0x{apploader_size:08X}\n\n")

        # Unknown stuff gleaned from YAGCD
        lines.append(f"debug_monitor_address: .long 0x{debug_monitor_address:08X}\n\n")

        # More padding
        lines.append(f".fill 0x18\n\n")

        # DOL and FST data
        lines.append(f"dol_offset: .long 0x{dol_offset:08X}\n")
        lines.append(f"fst_offset: .long 0x{fst_offset:08X}\n\n")

        lines.append(
            f"# The FST is only allocated once per game boot, even in games with multiple disks. fst_max_size is used to ensure that\n"
        )
        lines.append(
            f"# there is enough space allocated for the FST in the event that a game spans multiple disks, and one disk has a larger FST than another.\n"
        )
        lines.append(f"fst_size: .long 0x{fst_size:08X}\n")
        lines.append(f"fst_max_size: .long 0x{fst_max_size:08X}\n\n")

        # Honestly not sure what this data is for
        lines.append(f"# Not even YAGCD knows what these are for.\n")
        lines.append(f"user_position: .long 0x{user_position:08X}\n")
        lines.append(f"user_length: .long 0x{user_length:08X}\n")
        lines.append(f"unk_int: .long 0x{unk_int:08X}\n\n")

        # Final padding
        lines.append(f".word 0\n")
        out_path = self.out_path()

        out_path.parent.mkdir(parents=True, exist_ok=True)

        with open(out_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        return

    def should_split(self) -> bool:
        return True

    def out_path(self) -> Path:
        return options.opts.asm_path / "sys" / "boot.s"
