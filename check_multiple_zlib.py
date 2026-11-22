import zlib

with open('/home/user/Desktop/game-voice/extracted_PC/Paks/pakchunk0-WindowsNoEditor_9-GV-RU_P.pak', 'rb') as f:
    data = f.read()

# Decompress first stream from offset 0x59
compressed = data[0x59:]
decomp = zlib.decompressobj()
result = decomp.decompress(compressed)
result += decomp.flush()

print(f"First stream decompressed: {len(result)} bytes")
print(f"Unused data: {len(decomp.unused_data)} bytes")

# Check if there's more compressed data after the first stream
if decomp.unused_data:
    remaining = decomp.unused_data
    print(f"Remaining compressed data: {len(remaining)} bytes")
    print(f"First bytes of remaining: {remaining[:16].hex()}")
    
    # Try to decompress remaining
    try:
        decomp2 = zlib.decompressobj()
        result2 = decomp2.decompress(remaining)
        result2 += decomp2.flush()
        print(f"Second stream decompressed: {len(result2)} bytes")
        print(f"Unused after second: {len(decomp2.unused_data)} bytes")
        if result2:
            print(f"Second stream preview: {result2[:100]}")
    except Exception as e:
        print(f"Second stream failed: {e}")

# Also check the raw data after the first zlib stream in the original file
# The first stream ends at some offset in the compressed data
consumed = len(compressed) - len(decomp.unused_data)
print(f"\nFirst stream consumed {consumed} bytes of compressed data")
print(f"Original offset of next data: 0x{0x59 + consumed:x}")

# Check what's at that offset in the original file
next_offset = 0x59 + consumed
if next_offset < len(data):
    print(f"Data at 0x{next_offset:x}: {data[next_offset:next_offset+16].hex()}")

