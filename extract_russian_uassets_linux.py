#!/usr/bin/env python3
"""
Extract Russian localization .uasset files from PC GameVoice mod pakchunk0
Using Linux Oodle library (liboo2corelinux64.so.9)
"""
import os
import struct
import ctypes
import sys

# Oodle library (Linux)
OODLE_LIB_PATH = "/home/user/Desktop/game-voice/liboo2corelinux64.so.9"

try:
    OODLE = ctypes.CDLL(OODLE_LIB_PATH)
    OodleLZ_GetDecodeBufferSize = OODLE.OodleLZ_GetDecodeBufferSize
    OodleLZ_GetDecodeBufferSize.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    OodleLZ_GetDecodeBufferSize.restype = ctypes.c_size_t

    OodleLZ_Decompress = OODLE.OodleLZ_Decompress
    OodleLZ_Decompress.argtypes = [
        ctypes.c_void_p, ctypes.c_size_t,
        ctypes.c_void_p, ctypes.c_size_t,
        ctypes.c_int, ctypes.c_uint32, ctypes.c_int,
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_void_p, ctypes.c_size_t,
    ]
    OodleLZ_Decompress.restype = ctypes.c_size_t
    print(f"Loaded Oodle: {OODLE_LIB_PATH}")
except Exception as e:
    print(f"Failed to load Oodle: {e}")
    sys.exit(1)

MOD_DIR = "/home/user/Desktop/game-voice/extracted_PC/Paks"
OUTPUT_DIR = "/tmp/extracted_russian_uassets"

# Target asset paths (from PC mod asset registry)
TARGET_ASSETS = [
    "SwGame",
    "Narrative/LocalisedStrings/UI_Strings",
    "UI/Fonts/R8/R8_Menu_Captions",
    "UI/GameMenu/LoadableScreenWidgets/Settings_Audio_V2",
    "UI/GameMenu/LoadableScreenWidgets/Settings_Gameplay_V2",
    "UI/Credits/Credits_WIP_Export_Sheet",
    "Audio/Enums/SpeakerOutput",
]

def decompress_oodle(compressed_data):
    comp_buf = ctypes.create_string_buffer(compressed_data)
    raw_len = OodleLZ_GetDecodeBufferSize(comp_buf, len(compressed_data))
    if raw_len == 0 or raw_len > 100_000_000:
        return None
    raw_buf = ctypes.create_string_buffer(raw_len)
    result = OodleLZ_Decompress(
        comp_buf, len(compressed_data),
        raw_buf, raw_len,
        0, 0, 0, None, None, None, None, None, 0
    )
    if result == raw_len:
        return bytes(raw_buf)
    return None

def parse_utoc_9gvru(utoc_path):
    """Parse 9-GV-RU_P UTOC specifically"""
    with open(utoc_path, 'rb') as f:
        data = f.read()

    magic = data[:16]
    version = struct.unpack('<I', data[0x10:0x14])[0]
    header_size = struct.unpack('<I', data[0x14:0x18])[0]
    entry_count = struct.unpack('<I', data[0x18:0x1C])[0]
    entry_size = struct.unpack('<I', data[0x1C:0x20])[0]
    cb_count = struct.unpack('<I', data[0x20:0x24])[0]
    cb_entry_size = struct.unpack('<I', data[0x24:0x28])[0]

    print(f"  UTOC: version={version}, header_size={header_size}")
    print(f"  Entries: {entry_count} (size={entry_size}), CB: {cb_count} (size={cb_entry_size})")

    # Parse entries - 9-GV-RU_P has 3 entries of 17 bytes each
    # Entry format: 16 byte name hash + 1 byte flags (or similar)
    entries = []
    for i in range(entry_count):
        off = header_size + i * entry_size
        entry = data[off:off+entry_size]
        if len(entry) >= 17:
            name_hash = entry[:16]
            flags = entry[16]
            entries.append({'name_hash': name_hash, 'flags': flags})

    # The CB entries are NOT at 0x28 - they're after the string table
    # Find them by scanning for the pattern
    # From hex dump, CB entries start around 0xC0-0xD0
    # But cb_entry_size=0 means they might not be standard
    
    # For 9-GV-RU_P, the UCAS data is NOT Oodle compressed - it's raw
    # The actual asset data is in the 9-GV-RU_P.pak file (zlib streams)
    
    return {
        'entries': entries,
        'cb_entries': [],  # Not used for 9-GV-RU_P
        'container_id': data[0x30:0x38],
        'raw': data
    }

def parse_utoc_8gvru(utoc_path):
    """Parse 8-GV-RU_P UTOC specifically"""
    with open(utoc_path, 'rb') as f:
        data = f.read()

    magic = data[:16]
    version = struct.unpack('<I', data[0x10:0x14])[0]
    header_size = struct.unpack('<I', data[0x14:0x18])[0]
    entry_count = struct.unpack('<I', data[0x18:0x1C])[0]
    entry_size = struct.unpack('<I', data[0x1C:0x20])[0]
    cb_count = struct.unpack('<I', data[0x20:0x24])[0]
    cb_entry_size = struct.unpack('<I', data[0x24:0x28])[0]

    print(f"  UTOC: version={version}, header_size={header_size}")
    print(f"  Entries: {entry_count} (size={entry_size}), CB: {cb_count} (size={cb_entry_size})")

    # Parse CB entries - they start at 0x28 (after header fields)
    # Each CB entry is 8 bytes (offset:4, size:4) since cb_entry_size=1 means 8 bytes?
    cb_entries = []
    cb_start = 0x28
    for i in range(cb_count):
        off = cb_start + i * 8
        if off + 8 <= len(data):
            cb = data[off:off+8]
            cb_off = struct.unpack('<I', cb[0:4])[0]
            cb_sz = struct.unpack('<I', cb[4:8])[0]
            cb_entries.append({'offset': cb_off, 'size': cb_sz})
            print(f"    CB {i}: offset=0x{cb_off:x}, size=0x{cb_sz:x}")

    return {
        'entries': [],
        'cb_entries': cb_entries,
        'container_id': data[0x30:0x38],
        'raw': data
    }

def extract_from_8gvru(ucas_path, utoc_info, output_dir):
    """Extract uassets from 8-GV-RU_P Oodle blocks"""
    os.makedirs(output_dir, exist_ok=True)

    with open(ucas_path, 'rb') as f:
        ucas_data = f.read()

    print(f"  UCAS size: {len(ucas_data)} bytes")

    for i, cb in enumerate(utoc_info['cb_entries']):
        off = cb['offset']
        sz = cb['size']

        if off >= len(ucas_data) or sz == 0 or off + sz > len(ucas_data):
            print(f"    CB {i}: SKIP (offset=0x{off:x}, size=0x{sz:x})")
            continue

        block = ucas_data[off:off+sz]
        if len(block) == 0:
            continue

        print(f"    CB {i}: offset=0x{off:x}, size=0x{sz:x}, magic={block[0]:02x}")

        # Check for Oodle magic
        if block[0] in (0xCC, 0xCD, 0xCE, 0xCF, 0xC0, 0xC1, 0xC2, 0xC3, 0x8C, 0x8D, 0x8E, 0x8F):
            print(f"      Oodle compressed, decompressing...")
            decompressed = decompress_oodle(block)
            if decompressed:
                print(f"      Decompressed: {len(decompressed)} bytes")
                # Save for inspection
                out_path = os.path.join(output_dir, f'8gvru_block_{i:03d}.bin')
                with open(out_path, 'wb') as f:
                    f.write(decompressed)
                # Scan for uasset files
                scan_for_uassets(decompressed, output_dir, f'8gvru_block_{i:03d}_')
        else:
            print(f"      Not Oodle compressed")
            out_path = os.path.join(output_dir, f'8gvru_block_{i:03d}_raw.bin')
            with open(out_path, 'wb') as f:
                f.write(block)

def extract_from_9gvru_pak(pak_path, output_dir):
    """Extract uassets from 9-GV-RU_P.pak (concatenated zlib streams)"""
    os.makedirs(output_dir, exist_ok=True)

    with open(pak_path, 'rb') as f:
        data = f.read()

    print(f"  PAK size: {len(data)} bytes")

    # Decompress all zlib streams
    offset = 0x59  # First zlib stream starts here
    all_decompressed = b''
    stream_count = 0

    while offset < len(data):
        compressed = data[offset:]
        if len(compressed) < 2:
            break

        if compressed[0] != 0x78:
            # Find next zlib stream
            next_zlib = compressed.find(b'\x78\x9c')
            if next_zlib < 0:
                next_zlib = compressed.find(b'\x78\xda')
            if next_zlib < 0:
                next_zlib = compressed.find(b'\x78\x01')
            if next_zlib < 0:
                break
            offset += next_zlib
            continue

        try:
            decomp = zlib.decompressobj()
            result = decomp.decompress(compressed)
            result += decomp.flush()

            if len(result) > 0:
                all_decompressed += result
                stream_count += 1

            consumed = len(compressed) - len(decomp.unused_data)
            offset += consumed

            if consumed == 0:
                break

        except Exception as e:
            # Skip to next potential zlib stream
            next_zlib = compressed.find(b'\x78\x9c', 1)
            if next_zlib < 0:
                next_zlib = compressed.find(b'\x78\xda', 1)
            if next_zlib < 0:
                next_zlib = compressed.find(b'\x78\x01', 1)
            if next_zlib < 0:
                break
            offset += next_zlib

    print(f"  Total zlib streams: {stream_count}, total decompressed: {len(all_decompressed)} bytes")

    # Save full decompressed data
    with open(os.path.join(output_dir, '9gvru_pak_decompressed.bin'), 'wb') as f:
        f.write(all_decompressed)

    # Scan for uasset files
    scan_for_uassets(all_decompressed, output_dir, '9gvru_pak_')

def scan_for_uassets(data, output_dir, prefix):
    """Scan binary data for Unreal package headers"""
    import struct
    os.makedirs(output_dir, exist_ok=True)

    pos = 0
    found = 0
    while True:
        pos = data.find(b'\x00\x00\x00\x00', pos)
        if pos < 0:
            break
        if pos + 8 <= len(data):
            version = struct.unpack('<I', data[pos+4:pos+8])[0]
            if 100 <= version <= 2000:
                # Found potential uasset - extract from here to next header or 1MB
                next_pos = data.find(b'\x00\x00\x00\x00', pos + 4)
                if next_pos < 0:
                    next_pos = min(pos + 1000000, len(data))
                chunk = data[pos:next_pos]
                
                # Check for target asset names in this chunk
                for target in TARGET_ASSETS:
                    if target.encode('utf-8') in chunk:
                        safe_name = target.replace('/', '_').replace('.', '_') + '.uasset'
                        out_path = os.path.join(output_dir, f'{prefix}{safe_name}')
                        with open(out_path, 'wb') as f:
                            f.write(chunk)
                        print(f"    FOUND TARGET: {target} -> {safe_name} ({len(chunk)} bytes)")
                        found += 1
                        break
                else:
                    # Not a target, but save anyway for inspection (limit to first 20)
                    if found < 20:
                        out_path = os.path.join(output_dir, f'{prefix}uasset_{pos:08x}.uasset')
                        with open(out_path, 'wb') as f:
                            f.write(chunk[:min(500000, len(chunk))])
                        found += 1
        pos += 4

def main():
    print("=" * 60)
    print("EXTRACTING RUSSIAN UASSETS FROM PC GAMEVOICE MOD (Linux)")
    print("=" * 60)

    # Process 8-GV-RU_P (Oodle blocks in UCAS)
    print("\n--- 8-GV-RU_P ---")
    utoc_info = parse_utoc_8gvru(os.path.join(MOD_DIR, "pakchunk0-WindowsNoEditor_8-GV-RU_P.utoc"))
    extract_from_8gvru(
        os.path.join(MOD_DIR, "pakchunk0-WindowsNoEditor_8-GV-RU_P.ucas"),
        utoc_info,
        OUTPUT_DIR
    )

    # Process 9-GV-RU_P (zlib streams in .pak file)
    print("\n--- 9-GV-RU_P.pak ---")
    extract_from_9gvru_pak(
        os.path.join(MOD_DIR, "pakchunk0-WindowsNoEditor_9-GV-RU_P.pak"),
        OUTPUT_DIR
    )

    print(f"\nDone! Check {OUTPUT_DIR}/ for extracted .uasset files")
    print(f"Files extracted:")
    for root, dirs, files in os.walk(OUTPUT_DIR):
        for f in files:
            path = os.path.join(root, f)
            size = os.path.getsize(path)
            print(f"  {f} ({size} bytes)")

if __name__ == "__main__":
    import zlib
    main()
