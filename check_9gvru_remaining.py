with open('/home/user/Desktop/game-voice/extracted_PC/Paks/pakchunk0-WindowsNoEditor_9-GV-RU_P.pak', 'rb') as f:
    data = f.read()

# We know:
# - First zlib stream at 0x59, consumed 12235 bytes, produced 65536 bytes
# - Second zlib stream at 0x3024, produced 6395 bytes
# Let's check what's after the second stream

offset = 0x59
# First stream
compressed = data[offset:]
import zlib
decomp = zlib.decompressobj()
result1 = decomp.decompress(compressed)
result1 += decomp.flush()
consumed1 = len(compressed) - len(decomp.unused_data)
print(f"Stream 1: offset=0x{offset:x}, consumed={consumed1}, decompressed={len(result1)}")
offset += consumed1

# Second stream
compressed = data[offset:]
decomp = zlib.decompressobj()
result2 = decomp.decompress(compressed)
result2 += decomp.flush()
consumed2 = len(compressed) - len(decomp.unused_data)
print(f"Stream 2: offset=0x{offset:x}, consumed={consumed2}, decompressed={len(result2)}")
offset += consumed2

print(f"\nAfter 2 streams: offset=0x{offset:x} ({offset} bytes)")
print(f"Remaining data: {len(data) - offset} bytes")

# Check remaining data
remaining = data[offset:]
print(f"First 64 bytes of remaining: {remaining[:64].hex()}")

# Look for Oodle magic in remaining
oodle_magics = [0xCC, 0xCD, 0xCE, 0xCF, 0xC0, 0xC1, 0xC2, 0xC3, 0x8C, 0x8D, 0x8E, 0x8F]
for magic in oodle_magics:
    pos = remaining.find(bytes([magic]))
    if pos >= 0:
        print(f"  Oodle magic 0x{magic:02x} at remaining offset 0x{pos:x} (file offset 0x{offset+pos:x})")

# Also check if there are more zlib streams
for magic in [b'\x78\x9c', b'\x78\xda', b'\x78\x01']:
    pos = remaining.find(magic)
    if pos >= 0:
        print(f"  zlib magic {magic.hex()} at remaining offset 0x{pos:x} (file offset 0x{offset+pos:x})")

