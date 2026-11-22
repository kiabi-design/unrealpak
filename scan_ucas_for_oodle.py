import struct
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

with open('/home/user/Desktop/game-voice/extracted_PC/Paks/pakchunk0-WindowsNoEditor_8-GV-RU_P.ucas', 'rb') as f:
    ucas_data = f.read()

print(f"UCAS size: {len(ucas_data)} bytes")

# Scan for Oodle magic bytes
oodle_magics = [0xCC, 0xCD, 0xCE, 0xCF, 0xC0, 0xC1, 0xC2, 0xC3, 0x8C, 0x8D, 0x8E, 0x8F]
found = []
for magic in oodle_magics:
    pos = 0
    while True:
        pos = ucas_data.find(bytes([magic]), pos)
        if pos < 0:
            break
        found.append((pos, magic))
        pos += 1

found.sort(key=lambda x: x[0])
print(f"Found {len(found)} Oodle magic bytes:")
for pos, magic in found:
    print(f"  Offset 0x{pos:x}: magic=0x{magic:02x}")

# Try decompressing at each position
for pos, magic in found:
    if pos + 4 > len(ucas_data):
        continue
    # Try different sizes
    for size in [None, 10000, 50000, 100000]:
        if size is None:
            block = ucas_data[pos:]
        else:
            block = ucas_data[pos:pos+size]
        if len(block) < 4:
            continue
        print(f"\nTrying at 0x{pos:x} (size={len(block)}), magic=0x{magic:02x}")
        try:
            result = decompress_oodle(block)
            if result:
                print(f"  SUCCESS: {len(result)} bytes")
                # Check for uasset
                if b'\x00\x00\x00\x00' in result[:100]:
                    print(f"  CONTAINS UASSET MAGIC!")
                    # Save
                    with open(f'/tmp/ucas_oodle_0x{pos:x}.bin', 'wb') as f:
                        f.write(result)
                    break
        except Exception as e:
            print(f"  FAILED: {e}")

