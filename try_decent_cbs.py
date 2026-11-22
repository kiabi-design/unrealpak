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

# Try the DECENT CB entries from offset 0x28
cbs = [
    (0x20, 0x10000),   # At 0x28
    (0x10000, 0x148),  # At 0x2c
    (0x10148, 0x1),    # At 0x30
]

for i, (off, sz) in enumerate(cbs):
    if off + sz <= len(ucas_data):
        block = ucas_data[off:off+sz]
        print(f"CB {i}: offset=0x{off:x}, size=0x{sz:x}, magic={block[0]:02x} ({len(block)} bytes)")
        if block[0] in (0xCC, 0xCD, 0xCE, 0xCF, 0xC0, 0xC1, 0xC2, 0xC3, 0x8C, 0x8D, 0x8E, 0x8F):
            result = decompress_oodle(block)
            if result:
                print(f"  SUCCESS: {len(result)} bytes")
                with open(f'/tmp/8gvru_decent_{i}.bin', 'wb') as f:
                    f.write(result)
                # Scan for uasset
                pos = 0
                while True:
                    pos = result.find(b'\x00\x00\x00\x00', pos)
                    if pos < 0 or pos > len(result) - 8:
                        break
                    import struct
                    ver = struct.unpack('<I', result[pos+4:pos+8])[0]
                    if 100 <= ver <= 2000:
                        print(f"    UASSET at 0x{pos:x}, version={ver}")
                    pos += 4
            else:
                print(f"  FAILED")
        else:
            print(f"  Not Oodle magic")
            with open(f'/tmp/8gvru_decent_{i}_raw.bin', 'wb') as f:
                f.write(block)

# Also check what's at offset 0x0
print("\n--- Checking offset 0 ---")
block = ucas_data[0:0x20]
print(f"First 32 bytes: {block.hex()}")

