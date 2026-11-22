
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
