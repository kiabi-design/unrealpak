import ctypes

OODLE = ctypes.CDLL("/home/user/Desktop/game-voice/liboo2corelinux64.so.9")
OodleLZ_GetDecodeBufferSize = OODLE.OodleLZ_GetDecodeBufferSize
OodleLZ_GetDecodeBufferSize.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
OodleLZ_GetDecodeBufferSize.restype = ctypes.c_size_t
OodleLZ_Decompress = OODLE.OodleLZ_Decompress
OodleLZ_Decompress.argtypes = [
    ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t,
    ctypes.c_int, ctypes.c_uint32, ctypes.c_int, ctypes.c_void_p,
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t
]
OodleLZ_Decompress.restype = ctypes.c_size_t

def decompress_oodle(compressed_data):
    comp_buf = ctypes.create_string_buffer(compressed_data)
    raw_len = OodleLZ_GetDecodeBufferSize(comp_buf, len(compressed_data))
    if raw_len == 0 or raw_len > 100_000_000:
        return None
    raw_buf = ctypes.create_string_buffer(raw_len)
    result = OodleLZ_Decompress(comp_buf, len(compressed_data), raw_buf, raw_len, 0, 0, 0, None, None, None, None, None, 0)
    if result == raw_len:
        return bytes(raw_buf)
    return None

with open('/home/user/Desktop/game-voice/extracted_PC/Paks/pakchunk0-WindowsNoEditor_9-GV-RU_P.pak', 'rb') as f:
    data = f.read()

# Scan for Oodle magic in the remaining data (after offset 0x3024)
remaining = data[0x3024:]
print(f"Remaining data size: {len(remaining)} bytes")

# Find all Oodle magic bytes
oodle_magics = [0xCC, 0xCD, 0xCE, 0xCF, 0xC0, 0xC1, 0xC2, 0xC3, 0x8C, 0x8D, 0x8E, 0x8F]
found = []
for magic in oodle_magics:
    pos = 0
    while True:
        pos = remaining.find(bytes([magic]), pos)
        if pos < 0:
            break
        found.append((pos, magic))
        pos += 1

found.sort(key=lambda x: x[0])
print(f"Found {len(found)} Oodle magic bytes")
for pos, magic in found[:20]:
    print(f"  Offset 0x{pos:x} (0x{0x3024+pos:x} in file): magic=0x{magic:02x}")

# Try decompressing at each found position
for pos, magic in found[:10]:
    compressed = remaining[pos:]
    if len(compressed) < 4:
        continue
    print(f"\nTrying Oodle at remaining offset 0x{pos:x} (file 0x{0x3024+pos:x}), magic=0x{magic:02x}")
    try:
        result = decompress_oodle(compressed[:min(100000, len(compressed))])
        if result:
            print(f"  SUCCESS: {len(result)} bytes")
            # Check for asset names
            for target in ["UI_Strings", "R8_Menu_Captions", "Settings_Audio", "SwGame"]:
                if target.encode() in result:
                    print(f"    CONTAINS: {target}")
            break
    except Exception as e:
        print(f"  FAILED: {e}")

