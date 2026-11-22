with open('/home/user/Desktop/game-voice/extracted_PC/Paks/pakchunk0-WindowsNoEditor_9-GV-RU_P.pak', 'rb') as f:
    data = f.read()

# Skip zlib streams
offset = 0x36bc
remaining = data[offset:]

print("Parsing Oodle table in 9-GV-RU_P.pak...")
print(f"Table starts at file offset 0x{offset:x}")

# The table seems to have entries of 32 bytes each (from the hex dump)
# Each entry: magic(1) + ? + size/offset(8) + magic(1) + ? + size/offset(8)
# Let's parse it as 32-byte entries

pos = 0
entries = []
while pos + 32 <= len(remaining):
    chunk = remaining[pos:pos+32]
    magic1 = chunk[0]
    magic2 = chunk[16]
    
    # Check if both are Oodle magic
    oodle_magics = [0xCC, 0xCD, 0xCE, 0xCF, 0xC0, 0xC1, 0xC2, 0xC3, 0x8C, 0x8D, 0x8E, 0x8F]
    if magic1 in oodle_magics and magic2 in oodle_magics:
        # Parse the two 8-byte values (little endian)
        val1 = int.from_bytes(chunk[8:16], 'little')
        val2 = int.from_bytes(chunk[24:32], 'little')
        entries.append({
            'rel_offset': pos,
            'abs_offset': offset + pos,
            'magic1': magic1,
            'magic2': magic2,
            'val1': val1,
            'val2': val2,
            'raw': chunk.hex()
        })
    elif magic1 in oodle_magics:
        # Single entry?
        val1 = int.from_bytes(chunk[8:16], 'little')
        entries.append({
            'rel_offset': pos,
            'abs_offset': offset + pos,
            'magic1': magic1,
            'val1': val1,
            'raw': chunk.hex()
        })
    else:
        # Not a valid entry, might be end of table
        if pos > 100:  # After some valid entries
            break
    pos += 32

print(f"Found {len(entries)} table entries:")
for e in entries[:20]:
    if 'magic2' in e:
        print(f"  0x{e['abs_offset']:x}: magic={e['magic1']:02x}/{e['magic2']:02x}, val1=0x{e['val1']:x}, val2=0x{e['val2']:x}")
    else:
        print(f"  0x{e['abs_offset']:x}: magic={e['magic1']:02x}, val1=0x{e['val1']:x}")

# Now, the values might be offsets into the file where the actual Oodle data is
# Let's check what's at those offsets
print("\n--- Checking data at val1 offsets ---")
for e in entries[:10]:
    if e['val1'] > 0 and e['val1'] < len(data):
        target = data[e['val1']:e['val1']+16]
        print(f"  At val1=0x{e['val1']:x}: {target.hex()}")

# Also check if val1+val2 points to something
print("\n--- Checking if val1 is offset and val2 is size ---")
for e in entries[:10]:
    if 'val2' in e and e['val1'] > 0 and e['val1'] + e['val2'] <= len(data):
        target = data[e['val1']:e['val1']+min(32, e['val2'])]
        print(f"  Offset 0x{e['val1']:x}, size 0x{e['val2']:x}: {target.hex()}")

