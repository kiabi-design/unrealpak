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

with open('/home/user/Desktop/game-voice/extracted_PC/Paks/pakchunk0-WindowsNoEditor_8-GV-RU_P.utoc', 'rb') as f:
    data = f.read()

print(f"UTOC size: {len(data)} bytes")

# Parse header
magic = data[:16]
version = struct.unpack('<I', data[0x10:0x14])[0]
header_size = struct.unpack('<I', data[0x14:0x18])[0]
entry_count = struct.unpack('<I', data[0x18:0x1C])[0]
entry_size = struct.unpack('<I', data[0x1C:0x20])[0]
cb_count = struct.unpack('<I', data[0x20:0x24])[0]
cb_entry_size = struct.unpack('<I', data[0x24:0x28])[0]

print(f"Version: {version}")
print(f"Header size: {header_size} (0x{header_size:x})")
print(f"Entry count: {entry_count}, Entry size: {entry_size}")
print(f"CB count: {cb_count}, CB entry size: {cb_entry_size}")

# Container ID at 0x30
container_id = data[0x30:0x38]
print(f"Container ID: {container_id.hex()}")

# Parse entries (at header_size)
print(f"\n--- Entries (at 0x{header_size:x}) ---")
for i in range(entry_count):
    off = header_size + i * entry_size
    entry = data[off:off+entry_size]
    if len(entry) >= 12:
        offset = struct.unpack('<Q', entry[0:8])[0]
        size = struct.unpack('<I', entry[8:12])[0]
        print(f"  Entry {i}: offset=0x{offset:x}, size=0x{size:x}")

# The CB entries might NOT be at 0x28 - let's search for them
# In the hex dump, at 0xC0 there's data that looks like CB entries
print(f"\n--- Searching for CB entries ---")
# Look for patterns: offset (4 bytes) + size (4 bytes) where size is reasonable
for search_off in range(0x28, min(0x200, len(data)-8), 4):
    if search_off + 8 <= len(data):
        cb_off = struct.unpack('<I', data[search_off:search_off+4])[0]
        cb_sz = struct.unpack('<I', data[search_off+4:search_off+8])[0]
        if cb_sz > 0 and cb_sz < 1000000 and cb_off < 200000:
            print(f"  At 0x{search_off:x}: offset=0x{cb_off:x}, size=0x{cb_sz:x} (DECENT)")

# Also check the region around 0xC0-0x160 (from hex dump)
print(f"\n--- CB entries at 0xC0 ---")
for i in range(12):
    off = 0xC0 + i * 8
    if off + 8 <= len(data):
        cb_off = struct.unpack('<I', data[off:off+4])[0]
        cb_sz = struct.unpack('<I', data[off+4:off+8])[0]
        print(f"  CB {i}: offset=0x{cb_off:x}, size=0x{cb_sz:x}")

# Now try decompressing the blocks that look valid
print(f"\n--- Trying to decompress ---")
with open('/home/user/Desktop/game-voice/extracted_PC/Paks/pakchunk0-WindowsNoEditor_8-GV-RU_P.ucas', 'rb') as f:
    ucas_data = f.read()

print(f"UCAS size: {len(ucas_data)} bytes")

# Try the CB entries at 0xC0
for i in range(12):
    off = 0xC0 + i * 8
    if off + 8 <= len(data):
        cb_off = struct.unpack('<I', data[off:off+4])[0]
        cb_sz = struct.unpack('<I', data[off+4:off+8])[0]
        
        if cb_sz > 0 and cb_sz < 200000 and cb_off < len(ucas_data):
            block = ucas_data[cb_off:cb_off+cb_sz]
            if len(block) == cb_sz and block[0] in (0xCC, 0xCD, 0xCE, 0xCF, 0xC0, 0xC1, 0xC2, 0xC3, 0x8C, 0x8D, 0x8E, 0x8F):
                print(f"  CB {i}: offset=0x{cb_off:x}, size=0x{cb_sz:x}, magic={block[0]:02x} - TRYING OODLE")
                result = decompress_oodle(block)
                if result:
                    print(f"    SUCCESS: {len(result)} bytes")
                    # Check for uasset
                    if b'\x00\x00\x00\x00' in result[:100]:
                        print(f"    CONTAINS UASSET MAGIC!")
                    # Save
                    with open(f'/tmp/8gvru_block_{i}.bin', 'wb') as f:
                        f.write(result)
                else:
                    print(f"    FAILED")
            elif len(block) > 0:
                print(f"  CB {i}: offset=0x{cb_off:x}, size=0x{cb_sz:x}, magic={block[0]:02x} - not Oodle")

