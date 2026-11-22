with open('/home/user/Desktop/game-voice/extracted_PC/Paks/pakchunk0-WindowsNoEditor_9-GV-RU_P.pak', 'rb') as f:
    data = f.read()

offset = 0x36bc
remaining = data[offset:]

print("Parsing Oodle table (32-byte pairs)...")
pos = 0
entries = []
while pos + 32 <= len(remaining):
    chunk = remaining[pos:pos+32]
    # Each 16-byte half: 8 bytes padding + 8 bytes value
    val1 = int.from_bytes(chunk[8:16], 'little')
    val2 = int.from_bytes(chunk[24:32], 'little')
    
    # Check if values look like valid offsets/sizes
    if (val1 > 0 and val1 < len(data)) or (val2 > 0 and val2 < len(data)):
        entries.append({
            'rel_offset': pos,
            'abs_offset': offset + pos,
            'val1': val1,
            'val2': val2,
        })
    else:
        # Might be end of table
        if len(entries) > 10:
            break
    pos += 32

print(f"Found {len(entries)} valid entries:")
for e in entries[:30]:
    print(f"  0x{e['abs_offset']:x}: val1=0x{e['val1']:x} ({e['val1']}), val2=0x{e['val2']:x} ({e['val2']})")

# Check what's at val1 offsets (these might be offsets to Oodle data)
print("\n--- Data at val1 offsets ---")
for e in entries[:20]:
    if e['val1'] > 0 and e['val1'] < len(data):
        target = data[e['val1']:e['val1']+16]
        magic = target[0] if target else 0
        print(f"  0x{e['val1']:x}: magic=0x{magic:02x}, data={target.hex()}")

# Check if val1 is offset and val2 is size
print("\n--- If val1=offset, val2=size ---")
for e in entries[:20]:
    if e['val1'] > 0 and e['val2'] > 0 and e['val1'] + e['val2'] <= len(data):
        target = data[e['val1']:e['val1']+min(16, e['val2'])]
        magic = target[0] if target else 0
        print(f"  Offset 0x{e['val1']:x}, size 0x{e['val2']:x}: magic=0x{magic:02x}, data={target.hex()}")

