import zlib

with open('/home/user/Desktop/game-voice/extracted_PC/Paks/pakchunk0-WindowsNoEditor_9-GV-RU_P.pak', 'rb') as f:
    data = f.read()

# Start from offset 0x59 where first zlib stream begins
offset = 0x59
all_decompressed = b''
stream_count = 0

while offset < len(data):
    compressed = data[offset:]
    if len(compressed) < 2:
        break
    
    # Check for zlib magic (0x78 0x9c, 0x78 0xda, 0x78 0x01, etc.)
    if compressed[0] != 0x78:
        print(f"At offset 0x{offset:x}: not zlib magic ({compressed[0]:02x})")
        # Try to find next zlib stream
        next_zlib = compressed.find(b'\x78\x9c')
        if next_zlib < 0:
            next_zlib = compressed.find(b'\x78\xda')
        if next_zlib < 0:
            next_zlib = compressed.find(b'\x78\x01')
        if next_zlib < 0:
            break
        print(f"  Skipping {next_zlib} bytes to next zlib stream")
        offset += next_zlib
        continue
    
    try:
        decomp = zlib.decompressobj()
        result = decomp.decompress(compressed)
        result += decomp.flush()
        
        if len(result) > 0:
            all_decompressed += result
            stream_count += 1
            print(f"Stream {stream_count}: offset 0x{offset:x}, decompressed {len(result)} bytes, total {len(all_decompressed)}")
        
        consumed = len(compressed) - len(decomp.unused_data)
        offset += consumed
        
        if consumed == 0:
            print("No progress, breaking")
            break
            
    except Exception as e:
        print(f"Error at offset 0x{offset:x}: {e}")
        # Try to find next zlib stream
        next_zlib = compressed.find(b'\x78\x9c', 1)
        if next_zlib < 0:
            next_zlib = compressed.find(b'\x78\xda', 1)
        if next_zlib < 0:
            next_zlib = compressed.find(b'\x78\x01', 1)
        if next_zlib < 0:
            break
        offset += next_zlib

print(f"\nTotal streams: {stream_count}")
print(f"Total decompressed: {len(all_decompressed)} bytes")

with open('/tmp/9gvru_fully_decompressed.bin', 'wb') as f:
    f.write(all_decompressed)

# Check for uasset magic in the result
print("\nSearching for uasset magic in decompressed data...")
pos = 0
uasset_count = 0
while True:
    pos = all_decompressed.find(b'\x00\x00\x00\x00', pos)
    if pos < 0:
        break
    if pos + 8 <= len(all_decompressed):
        import struct
        version = struct.unpack('<I', all_decompressed[pos+4:pos+8])[0]
        if 100 <= version <= 2000:
            print(f"  Potential uasset at 0x{pos:x}, version={version}")
            uasset_count += 1
    pos += 4

print(f"Total potential uassets: {uasset_count}")

# Also search for legacy magic
pos = 0
while True:
    pos = all_decompressed.find(b'\xc1\x83\x2a\x9e', pos)
    if pos < 0:
        break
    print(f"  Legacy package at 0x{pos:x}")
    pos += 4

