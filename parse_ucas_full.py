with open('/home/user/Desktop/game-voice/extracted_PC/Paks/pakchunk0-WindowsNoEditor_9-GV-RU_P.ucas', 'rb') as f:
    data = f.read()

print(f"UCAS size: {len(data)} bytes")

# The UCAS seems to have:
# - Header (0x40 bytes)
# - Asset paths (null-terminated, starting at 0x40)
# - Then binary data

# Find all null-terminated strings that look like asset paths
paths = []
pos = 0x40
while pos < len(data):
    if data[pos] == 0:
        pos += 1
        continue
    end = data.find(b'\x00', pos)
    if end < 0 or end > pos + 200:
        pos += 1
        continue
    s = data[pos:end]
    try:
        decoded = s.decode('utf-8')
        if decoded.startswith('/Game/') or decoded.startswith('/Script/'):
            paths.append((pos, end, decoded))
    except:
        pass
    pos = end + 1

print(f"Found {len(paths)} asset paths")
for p in paths[:20]:
    print(f"  0x{p[0]:x}-0x{p[1]:x}: {p[2]}")

# Now check what's between paths
print("\nData between paths:")
for i in range(len(paths)-1):
    start = paths[i][1] + 1
    end = paths[i+1][0]
    if end > start:
        chunk = data[start:end]
        if len(chunk) > 10:
            print(f"  0x{start:x}-0x{end:x} ({len(chunk)} bytes): {chunk[:64].hex()}")

# Check last path to end of file
last_end = paths[-1][1] + 1
if last_end < len(data):
    chunk = data[last_end:]
    print(f"  0x{last_end:x}-end ({len(chunk)} bytes): {chunk[:64].hex()}")

