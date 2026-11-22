with open('/home/user/Desktop/game-voice/extracted_PC/Paks/pakchunk0-WindowsNoEditor_9-GV-RU_P.pak', 'rb') as f:
    data = f.read()

# Skip the two zlib streams
offset = 0x36bc
remaining = data[offset:]

# Look for Oodle block boundaries - they usually have a size prefix
# Let's scan for valid Oodle blocks by trying to decompress at each magic byte
# but with limited sizes

oodle_magics = [0xCC, 0xCD, 0xCE, 0xCF, 0xC0, 0xC1, 0xC2, 0xC3, 0x8C, 0x8D, 0x8E, 0x8F]

print("Scanning for Oodle blocks in 9-GV-RU_P.pak (after zlib streams)...")
print(f"Search range: 0x{offset:x} to 0x{len(data):x}")

for magic in oodle_magics:
    pos = 0
    while True:
        pos = remaining.find(bytes([magic]), pos)
        if pos < 0:
            break
        abs_pos = offset + pos
        # Check if there's enough data after this for a valid block
        if pos + 4 <= len(remaining):
            # Try to read potential size from the block header
            # Oodle doesn't have a standard size prefix, but let's check
            pass
        print(f"  File offset 0x{abs_pos:x} (rel 0x{pos:x}): magic=0x{magic:02x}")
        pos += 1

# Also look at the data structure around the first few magic bytes
for rel_pos in [0x3c, 0x7c, 0xdd, 0x17c, 0x1fc]:
    abs_pos = offset + rel_pos
    if abs_pos + 32 <= len(data):
        chunk = data[abs_pos:abs_pos+32]
        print(f"\nAt 0x{abs_pos:x}: {chunk.hex()}")

