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

# Skip the two zlib streams
offset = 0x36bc
remaining = data[offset:]
print(f"Remaining data: {len(remaining)} bytes")

# Try Oodle at the first found position: 0x8d at remaining offset 0x3c
for rel_offset in [0x3c, 0x7c, 0xdd, 0x17c, 0x1fc, 0x4fd, 0x57d, 0x5bd, 0x5ed, 0x853, 0x897]:
    abs_offset = offset + rel_offset
    if abs_offset >= len(data):
        continue
    block = data[abs_offset:]
    if len(block) < 4:
        continue
    print(f"\nTrying Oodle at file offset 0x{abs_offset:x} (rel 0x{rel_offset:x}), magic={block[0]:02x}, size={len(block)}")
    try:
        result = decompress_oodle(block[:min(200000, len(block))])
        if result:
            print(f"  SUCCESS: {len(result)} bytes")
            # Check for uasset
            if b'\x00\x00\x00\x00' in result[:100]:
                print(f"  CONTAINS UASSET MAGIC!")
            for target in ["UI_Strings", "R8_Menu_Captions", "Settings_Audio", "SwGame", "Narrative", "LocalisedStrings", "/Game/"]:
                if target.encode() in result:
                    print(f"  CONTAINS: {target}")
            with open(f'/tmp/9gvru_oodle_0x{abs_offset:x}.bin', 'wb') as f:
                f.write(result)
            break
        else:
            print(f"  FAILED (no result)")
    except Exception as e:
        print(f"  ERROR: {e}")

# Also try the zlib streams
import zlib
for rel_offset in [0x6d91, 0x4251, 0x162cd]:
    abs_offset = offset + rel_offset
    if abs_offset >= len(data):
        continue
    block = data[abs_offset:]
    print(f"\nTrying zlib at file offset 0x{abs_offset:x} (rel 0x{rel_offset:x}), magic={block[:2].hex()}")
    try:
        decomp = zlib.decompressobj()
        result = decomp.decompress(block)
        result += decomp.flush()
        if len(result) > 0:
            print(f"  SUCCESS: {len(result)} bytes")
            for target in ["UI_Strings", "R8_Menu_Captions", "Settings_Audio", "SwGame", "Narrative", "LocalisedStrings"]:
                if target.encode() in result:
                    print(f"  CONTAINS: {target}")
            with open(f'/tmp/9gvru_zlib_0x{abs_offset:x}.bin', 'wb') as f:
                f.write(result)
    except Exception as e:
        print(f"  FAILED: {e}")

