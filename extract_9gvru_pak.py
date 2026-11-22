import zlib

with open('/home/user/Desktop/game-voice/extracted_PC/Paks/pakchunk0-WindowsNoEditor_9-GV-RU_P.pak', 'rb') as f:
    data = f.read()

# Decompress from offset 0x59 (where zlib stream starts)
compressed = data[0x59:]
print(f"Compressed size: {len(compressed)}")

# Try decompress all
try:
    decompressed = zlib.decompress(compressed)
    print(f"Decompressed size: {len(decompressed)}")
    with open('/tmp/9gvru_decompressed.bin', 'wb') as f:
        f.write(decompressed)
    print("Written to /tmp/9gvru_decompressed.bin")
except Exception as e:
    print(f"Failed: {e}")
    # Try decompress in chunks
    decomp = zlib.decompressobj()
    result = b''
    chunk_size = 1024*1024
    for i in range(0, len(compressed), chunk_size):
        chunk = compressed[i:i+chunk_size]
        result += decomp.decompress(chunk)
    result += decomp.flush()
    print(f"Chunked decompressed size: {len(result)}")
    with open('/tmp/9gvru_decompressed.bin', 'wb') as f:
        f.write(result)

