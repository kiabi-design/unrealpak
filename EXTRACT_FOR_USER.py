#!/usr/bin/env python3
"""
EXTRACTION SCRIPTS FOR USER TO RUN LOCALLY
==========================================
Run these on your machine (PC or PS4) where you have the game files.
Then send me the extracted files (MB size, not GB).
"""

# ============================================================
# SCRIPT 1: Extract 536 English .wem from PS4 pakchunk2-ps4.pak
# ============================================================
# Requirements:
#   - PS4 pakchunk2-ps4.pak (815 MB)
#   - pak_filelist.txt (already have)
#   - ps4_pakchunk2_wwise_to_offset.json (already have)
#   - pak_replacements.json (already have)

SCRIPT1 = r'''
#!/usr/bin/env python3
"""
Extract 536 specific .wem files from PS4 pakchunk2-ps4.pak
Run this on your PC where you have the PS4 game files.
"""
import os
import json
import struct

# === CONFIGURE THESE PATHS ===
PAK_PATH = "pakchunk2-ps4.pak"           # Your PS4 pakchunk2 (815 MB)
FILELIST_PATH = "pak_filelist.txt"        # From earlier extraction
REPLACEMENTS_PATH = "pak_replacements.json"  # From this project
OUTPUT_DIR = "extracted_english_wem"      # Where to save extracted files
# ===============================

def parse_filelist(filelist_path):
    """Parse pak_filelist.txt to get filename -> offset, size"""
    mapping = {}
    with open(filelist_path, 'r') as f:
        for line in f:
            line = line.strip()
            if 'offset:' in line and 'size:' in line:
                # Format: LogPakFile: Display: "1000009927.wem" offset: 0, size: 6404, sha1: ...
                parts = line.split('"')
                if len(parts) >= 2:
                    filename = parts[1]
                    # Extract offset and size
                    import re
                    offset_match = re.search(r'offset:\s*(\d+)', line)
                    size_match = re.search(r'size:\s*(\d+)', line)
                    if offset_match and size_match:
                        offset = int(offset_match.group(1))
                        size = int(size_match.group(1))
                        mapping[filename] = (offset, size)
    return mapping

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Loading filelist...")
    filelist = parse_filelist(FILELIST_PATH)
    print(f"Loaded {len(filelist)} entries from filelist")

    print("Loading replacements...")
    with open(REPLACEMENTS_PATH, 'r') as f:
        replacements = json.load(f)
    print(f"Loaded {len(replacements)} replacements")

    print(f"Opening {PAK_PATH}...")
    with open(PAK_PATH, 'rb') as pak:
        extracted = 0
        for wwise_id, info in replacements.items():
            filename = f"{wwise_id}.wem"
            if filename in filelist:
                offset, size = filelist[filename]
                pak.seek(offset)
                data = pak.read(size)

                out_path = os.path.join(OUTPUT_DIR, filename)
                with open(out_path, 'wb') as f:
                    f.write(data)
                extracted += 1

                if extracted % 50 == 0:
                    print(f"  Extracted {extracted}/{len(replacements)}...")
            else:
                print(f"  WARNING: {filename} not in filelist")

        print(f"\nDone! Extracted {extracted} .wem files to {OUTPUT_DIR}/")
        print(f"Total size: {sum(os.path.getsize(os.path.join(OUTPUT_DIR, f)) for f in os.listdir(OUTPUT_DIR)) / 1024 / 1024:.1f} MB")

if __name__ == "__main__":
    main()
'''

# ============================================================
# SCRIPT 2: Extract Russian .uasset from PC GameVoice mod pakchunk0
# ============================================================
# Requirements:
#   - PC GameVoice mod extracted (pakchunk0-WindowsNoEditor_8/9-GV-RU_P.utoc/.ucas)
#   - Oodle library (oo2core_9_win64.dll on Windows)

SCRIPT2 = r'''
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
'''

# ============================================================
# SCRIPT 3: Extract ALL 536 Russian .wem from PC GameVoice mod pakchunk2
# ============================================================
# Alternative to Script 1 if PC mod is easier

SCRIPT3 = r'''
#!/usr/bin/env python3
"""
Extract ALL Russian .wem files from PC GameVoice pakchunk2 (1.3 GB)
Run on Windows with Oodle DLL.
"""
import os
import struct
import ctypes

# === CONFIGURE ===
PAK_PATH = "extracted_PC/Paks/pakchunk2-WindowsNoEditor_9-GV-RU_P.pak"
OUTPUT_DIR = "extracted_russian_wem_all"
OODLE_DLL = "oo2core_9_win64.dll"
# ===================

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
except Exception as e:
    print(f"Oodle load failed: {e}")
    exit(1)

def decompress_oodle(data):
    comp_buf = ctypes.create_string_buffer(data)
    raw_len = OodleLZ_GetDecodeBufferSize(comp_buf, len(data))
    if raw_len == 0 or raw_len > 200_000_000:
        return None
    raw_buf = ctypes.create_string_buffer(raw_len)
    result = OodleLZ_Decompress(comp_buf, len(data), raw_buf, raw_len, 0, 0, 0, None, None, None, None, None, 0)
    if result == raw_len:
        return bytes(raw_buf)
    return None

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Reading {PAK_PATH}...")
    with open(PAK_PATH, 'rb') as f:
        # Read footer (last 204 bytes)
        f.seek(-204, 2)
        footer = f.read(204)

    magic = struct.unpack('<I', footer[0:4])[0]
    version = struct.unpack('<i', footer[4:8])[0]
    index_offset = struct.unpack('<q', footer[8:16])[0]
    index_size = struct.unpack('<q', footer[16:24])[0]
    enc_guid = footer[44:60]

    print(f"Pak version: {version}, Index: 0x{index_offset:x} size: 0x{index_size:x}")
    print(f"Encrypted: {enc_guid.hex() != '00'*16}")

    # Read encrypted index
    with open(PAK_PATH, 'rb') as f:
        f.seek(index_offset)
        encrypted_index = f.read(index_size)

    # Decrypt with PC AES key
    from Crypto.Cipher import AES
    key = bytes.fromhex("B17BD67644BCC561DD92EE5C23D9C371B2826098AFFFDBAF28A576FBFD5C2168")
    cipher = AES.new(key, AES.MODE_ECB)

    decrypted = b''
    for i in range(0, len(encrypted_index), 16):
        block = encrypted_index[i:i+16]
        if len(block) == 16:
            decrypted += cipher.decrypt(block)
        else:
            decrypted += block

    # Parse index entries (skip first 4 bytes)
    pos = 4
    wem_files = []

    while pos < len(decrypted):
        name_end = decrypted.find(b'\x00', pos)
        if name_end < 0 or name_end == pos:
            break
        name = decrypted[pos:name_end].decode('utf-8', errors='ignore')
        pos = name_end + 1

        if pos + 41 > len(decrypted):
            break

        offset = struct.unpack('<Q', decrypted[pos:pos+8])[0]
        size = struct.unpack('<Q', decrypted[pos+8:pos+16])[0]
        comp_method = struct.unpack('<I', decrypted[pos+36:pos+40])[0]
        comp_size = struct.unpack('<Q', decrypted[pos+40:pos+48])[0]
        encrypted = decrypted[pos+48]
        pos += 49

        if name.endswith('.wem'):
            wem_files.append({
                'name': name,
                'offset': offset,
                'size': size,
                'comp_method': comp_method,
                'comp_size': comp_size
            })

    print(f"Found {len(wem_files)} .wem files in index")

    # Extract each .wem
    with open(PAK_PATH, 'rb') as f:
        for i, wem in enumerate(wem_files):
            f.seek(wem['offset'])
            data = f.read(wem['comp_size'] if wem['comp_size'] > 0 else wem['size'])

            # Decompress if needed
            if wem['comp_method'] == 3:  # Oodle
                data = decompress_oodle(data)
                if data is None:
                    print(f"  [{i+1}/{len(wem_files)}] FAILED to decompress {wem['name']}")
                    continue

            out_path = os.path.join(OUTPUT_DIR, os.path.basename(wem['name']))
            with open(out_path, 'wb') as out:
                out.write(data)

            if (i + 1) % 50 == 0:
                print(f"  Extracted {i+1}/{len(wem_files)}...")

    print(f"\nDone! Extracted {len(wem_files)} Russian .wem files to {OUTPUT_DIR}/")

if __name__ == "__main__":
    main()
'''

# Write all scripts
with open("extract_english_wem_from_ps4.py", "w") as f:
    f.write(SCRIPT1)
print("Created: extract_english_wem_from_ps4.py")

with open("extract_russian_uassets_from_pc.py", "w") as f:
    f.write(SCRIPT2)
print("Created: extract_russian_uassets_from_pc.py")

with open("extract_all_russian_wem_from_pc.py", "w") as f:
    f.write(SCRIPT3)
print("Created: extract_all_russian_wem_from_pc.py")

print("\n" + "="*60)
print("NEXT STEPS FOR YOU:")
print("="*60)
print("""
1. COPY THESE 3 SCRIPTS to your machine with the game files
2. ALSO COPY these required files:
   - pak_filelist.txt
   - pak_replacements.json
   - ps4_pakchunk2_wwise_to_offset.json
   - oo2core_9_win64.dll (for scripts 2 & 3)

3. RUN SCRIPT 1 (on machine with PS4 pakchunk2-ps4.pak):
   python3 extract_english_wem_from_ps4.py
   -> Produces: extracted_english_wem/ (536 .wem files, ~MB)

4. RUN SCRIPT 2 (on Windows with PC GameVoice mod):
   python3 extract_russian_uassets_from_pc.py
   -> Produces: extracted_russian_uassets/ (~38 .uasset files)

5. OPTIONAL: RUN SCRIPT 3 (alternative, gets ALL 536 Russian .wem from PC mod):
   python3 extract_all_russian_wem_from_pc.py
   -> Produces: extracted_russian_wem_all/ (536 .wem files)

6. SEND ME the extracted folders (they're small - MB not GB)
7. I'LL BUILD the final 6 PS4 files
""")