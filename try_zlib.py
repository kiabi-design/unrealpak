import zlib
import struct

with open('/home/user/Desktop/game-voice/extracted_PC/Paks/pakchunk0-WindowsNoEditor_9-GV-RU_P.pak', 'rb') as f:
    data = f.read()

print(f"Total size: {len(data)}")

# Try zlib at offset 0x50
for offset in [0x50, 0x58, 0x60, 0x40]:
    if offset >= len(data):
        continue
    compressed = data[offset:]
    if len(compressed) < 2:
        continue
    print(f"\nTrying offset 0x{offset:x}: first bytes {compressed[0]:02x} {compressed[1]:02x}")
    try:
        decompressed = zlib.decompress(compressed)
        print(f"  SUCCESS: {len(decompressed)} bytes")
        # Check for uasset magic
        if b'\x00\x00\x00\x00' in decompressed[:100]:
            print("  Contains uasset magic!")
        with open(f'/tmp/test_decompressed_0x{offset:x}.bin', 'wb') as f:
            f.write(decompressed)
        break
    except Exception as e:
        print(f"  FAILED: {e}")

# Also try gzip
import gzip
for offset in [0x50, 0x58]:
    if offset >= len(data):
        continue
    compressed = data[offset:]
    try:
        decompressed = gzip.decompress(compressed)
        print(f"  GZIP at 0x{offset:x} SUCCESS: {len(decompressed)} bytes")
        with open(f'/tmp/test_gzip_0x{offset:x}.bin', 'wb') as f:
            f.write(decompressed)
        break
    except Exception as e:
        print(f"  GZIP at 0x{offset:x} FAILED: {e}")
