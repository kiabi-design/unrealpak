
#!/usr/bin/env python3
"""
Extract Russian localization .uasset files from PC GameVoice mod pakchunk0
Run this on Windows where Oodle DLL works.
"""
import os
import struct
import ctypes
import sys

# === CONFIGURE THESE PATHS ===
MOD_DIR = "extracted_PC/Paks"  # Where PC mod files are
OUTPUT_DIR = "extracted_russian_uassets"
# ===============================

# Oodle library (Windows)
OODLE_DLL = "oo2core_9_win64.dll"  # Put next to script or in PATH

try:
    OODLE = ctypes.CDLL(OODLE_DLL)
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
    print(f"Loaded Oodle: {OODLE_DLL}")
except Exception as e:
    print(f"Failed to load Oodle: {e}")
    sys.exit(1)

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

def parse_utoc(utoc_path):
    with open(utoc_path, 'rb') as f:
        data = f.read()

    magic = data[:16]
    version = struct.unpack('<I', data[0x10:0x14])[0]
    header_size = struct.unpack('<I', data[0x14:0x18])[0]
    entry_count = struct.unpack('<I', data[0x18:0x1C])[0]
    entry_size = struct.unpack('<I', data[0x1C:0x20])[0]
    cb_count = struct.unpack('<I', data[0x20:0x24])[0]
    cb_entry_size = struct.unpack('<I', data[0x24:0x28])[0]

    # Container ID
    container_id = data[0x30:0x38]

    # Parse entries (17 bytes: offset:8, size:8, comp:1)
    entries = []
    for i in range(entry_count):
        off = header_size + i * entry_size
        entry = data[off:off+entry_size]
        if len(entry) >= 17:
            offset = struct.unpack('<Q', entry[0:8])[0]
            size = struct.unpack('<Q', entry[8:16])[0]
            comp = entry[16]
            entries.append({'offset': offset, 'size': size, 'comp': comp})

    # Parse compressed block entries (8 bytes each at 0x28)
    cb_entries = []
    for i in range(cb_count):
        off = 0x28 + i * 8
        cb = data[off:off+8]
        cb_off = struct.unpack('<I', cb[0:4])[0]
        cb_sz = struct.unpack('<I', cb[4:8])[0]
        cb_entries.append({'offset': cb_off, 'size': cb_sz})

    return {
        'entries': entries,
        'cb_entries': cb_entries,
        'container_id': container_id
    }

def extract_uassets(ucas_path, utoc_info, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    with open(ucas_path, 'rb') as f:
        ucas_data = f.read()

    # Decompress each block
    for i, cb in enumerate(utoc_info['cb_entries']):
        off = cb['offset']
        sz = cb['size']

        if off >= len(ucas_data) or off + sz > len(ucas_data):
            continue

        block = ucas_data[off:off+sz]
        if len(block) == 0:
            continue

        # Check for Oodle magic
        if block[0] in (0xCC, 0xCD, 0xCE, 0xCF, 0xC0, 0xC1, 0xC2, 0xC3):
            decompressed = decompress_oodle(block)
            if decompressed:
                # Scan for uasset files in decompressed data
                pos = 0
                while True:
                    pos = decompressed.find(b'\x00\x00\x00\x00', pos)
                    if pos < 0:
                        break

                    # Try to find asset name after header
                    # Look for our target paths
                    for target in TARGET_ASSETS:
                        target_bytes = target.encode('utf-8')
                        name_pos = decompressed.find(target_bytes, pos, pos + 5000)
                        if name_pos >= 0:
                            # Found! Extract reasonable chunk
                            chunk_start = max(0, pos - 100)
                            chunk_end = min(len(decompressed), pos + 500000)
                            chunk = decompressed[chunk_start:chunk_end]

                            safe_name = target.replace('/', '_').replace('.', '_') + '.uasset'
                            out_path = os.path.join(output_dir, safe_name)
                            with open(out_path, 'wb') as f:
                                f.write(chunk)
                            print(f"  Extracted: {target} -> {safe_name} ({len(chunk)} bytes)")

                    pos += 4

def main():
    print("=" * 60)
    print("EXTRACTING RUSSIAN UASSETS FROM PC GAMEVOICE MOD")
    print("=" * 60)

    # Process both 8-GV-RU_P and 9-GV-RU_P
    for suffix in ['8-GV-RU_P', '9-GV-RU_P']:
        print(f"\n--- {suffix} ---")
        utoc_path = os.path.join(MOD_DIR, f"pakchunk0-WindowsNoEditor_{suffix}.utoc")
        ucas_path = os.path.join(MOD_DIR, f"pakchunk0-WindowsNoEditor_{suffix}.ucas")

        if not os.path.exists(utoc_path) or not os.path.exists(ucas_path):
            print(f"  Files not found, skipping")
            continue

        print(f"  Parsing UTOC...")
        utoc_info = parse_utoc(utoc_path)
        print(f"    Entries: {len(utoc_info['entries'])}, CB: {len(utoc_info['cb_entries'])}")

        print(f"  Extracting from UCAS...")
        extract_uassets(ucas_path, utoc_info, OUTPUT_DIR)

    print(f"\nDone! Check {OUTPUT_DIR}/ for extracted .uasset files")

if __name__ == "__main__":
    main()
