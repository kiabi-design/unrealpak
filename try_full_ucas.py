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
print(f"First 32 bytes: {ucas_data[:32].hex()}")

# Try from offset 0 (magic 0xCC)
print("\n--- Trying from offset 0 ---")
result = decompress_oodle(ucas_data)
if result:
    print(f"SUCCESS: {len(result)} bytes")
    with open('/tmp/ucas_full_decompressed.bin', 'wb') as f:
        f.write(result)
    # Check for uasset
    if b'\x00\x00\x00\x00' in result[:100]:
        print("CONTAINS UASSET MAGIC!")
    # Scan for asset names
    for target in ["UI_Strings", "R8_Menu_Captions", "Settings_Audio", "SwGame", "Narrative", "LocalisedStrings"]:
        if target.encode() in result:
            print(f"  CONTAINS: {target}")
else:
    print("FAILED")

# Try from offset 0x71 (where the large block starts)
print("\n--- Trying from offset 0x71 ---")
block = ucas_data[0x71:]
print(f"Block size: {len(block)}, magic: {block[0]:02x}")
result = decompress_oodle(block)
if result:
    print(f"SUCCESS: {len(result)} bytes")
    with open('/tmp/ucas_0x71_decompressed.bin', 'wb') as f:
        f.write(result)
    for target in ["UI_Strings", "R8_Menu_Captions", "Settings_Audio", "SwGame", "Narrative", "LocalisedStrings"]:
        if target.encode() in result:
            print(f"  CONTAINS: {target}")
else:
    print("FAILED")

