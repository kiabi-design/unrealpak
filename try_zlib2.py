import zlib

with open('/home/user/Desktop/game-voice/extracted_PC/Paks/pakchunk0-WindowsNoEditor_9-GV-RU_P.pak', 'rb') as f:
    data = f.read()

# The zlib magic 0x78 0x9c is at offset 0x58
# But there's 8 bytes before it (at 0x50): 00 00 00 00 00 00 00 01
# Let's try from 0x58
compressed = data[0x58:]
print(f"Trying zlib from offset 0x58, length={len(compressed)}, first bytes: {compressed[:4].hex()}")

try:
    decompressed = zlib.decompress(compressed)
    print(f"SUCCESS: {len(decompressed)} bytes")
    with open('/tmp/test_decompressed_pak.bin', 'wb') as f:
        f.write(decompressed)
    # Check for uasset magic
    for i in range(min(10, len(decompressed)//1000)):
        pos = decompressed.find(b'\x00\x00\x00\x00', i*1000)
        if pos >= 0:
            print(f"  Found uasset magic at 0x{pos:x}")
except Exception as e:
    print(f"FAILED: {e}")

# Also try from 0x50 with the 8-byte prefix removed
compressed2 = data[0x50:]
print(f"\nTrying zlib from offset 0x50, length={len(compressed2)}, first bytes: {compressed2[:4].hex()}")

try:
    decompressed = zlib.decompress(compressed2)
    print(f"SUCCESS: {len(decompressed)} bytes")
except Exception as e:
    print(f"FAILED: {e}")

# Try raw deflate (skip zlib header)
import zlib
compressed3 = data[0x58+2:]  # Skip 0x78 0x9c
print(f"\nTrying raw deflate from offset 0x5a, length={len(compressed3)}")
try:
    decompressed = zlib.decompress(compressed3, -zlib.MAX_WBITS)
    print(f"SUCCESS: {len(decompressed)} bytes")
except Exception as e:
    print(f"FAILED: {e}")
