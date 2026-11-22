import zlib

with open('/home/user/Desktop/game-voice/extracted_PC/Paks/pakchunk0-WindowsNoEditor_9-GV-RU_P.pak', 'rb') as f:
    data = f.read()

# Try from offset 0x59 (where 0x78 0x9c actually is)
for offset in [0x59, 0x58, 0x5a]:
    compressed = data[offset:]
    print(f"Trying offset 0x{offset:x}, first bytes: {compressed[:4].hex()}")
    try:
        decompressed = zlib.decompress(compressed)
        print(f"  SUCCESS: {len(decompressed)} bytes")
        with open(f'/tmp/test_dec_0x{offset:x}.bin', 'wb') as f:
            f.write(decompressed)
        break
    except Exception as e:
        print(f"  FAILED: {e}")

# Also try the Oodle library on this
import ctypes
OODLE_LIB = ctypes.CDLL("/home/user/Desktop/game-voice/liboo2corelinux64.so.9")
OodleLZ_GetDecodeBufferSize = OODLE_LIB.OodleLZ_GetDecodeBufferSize
OodleLZ_GetDecodeBufferSize.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
OodleLZ_GetDecodeBufferSize.restype = ctypes.c_size_t
OodleLZ_Decompress = OODLE_LIB.OodleLZ_Decompress
OodleLZ_Decompress.argtypes = [
    ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t,
    ctypes.c_int, ctypes.c_uint32, ctypes.c_int, ctypes.c_void_p,
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t
]
OodleLZ_Decompress.restype = ctypes.c_size_t

def decompress_oodle(compressed_data):
    comp_buf = ctypes.create_string_buffer(compressed_data)
    raw_len = OodleLZ_GetDecodeBufferSize(comp_buf, len(compressed_data))
    if raw_len == 0:
        raise ValueError("Failed to get decode buffer size")
    raw_buf = ctypes.create_string_buffer(raw_len)
    result = OodleLZ_Decompress(comp_buf, len(compressed_data), raw_buf, raw_len, 0, 0, 0, None, None, None, None, None, 0)
    if result != raw_len:
        raise ValueError(f"Decompression failed: expected {raw_len}, got {result}")
    return bytes(raw_buf)

# Try Oodle on the pak data from various offsets
for offset in [0x50, 0x58, 0x59, 0x40]:
    compressed = data[offset:]
    if len(compressed) < 4:
        continue
    print(f"\nTrying Oodle at offset 0x{offset:x}, magic={compressed[0]:02x}")
    if compressed[0] in (0xCC, 0xCD, 0xCE, 0xCF, 0xC0, 0xC1, 0xC2, 0xC3, 0x8C, 0x8D, 0x8E, 0x8F):
        try:
            decompressed = decompress_oodle(compressed)
            print(f"  SUCCESS: {len(decompressed)} bytes")
            with open(f'/tmp/test_oodle_0x{offset:x}.bin', 'wb') as f:
                f.write(decompressed)
            break
        except Exception as e:
            print(f"  FAILED: {e}")
    else:
        print(f"  Not Oodle magic")

