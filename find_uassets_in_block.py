import struct

with open('/tmp/pakchunk0_extracted/8-GV-RU_P/block_009.bin', 'rb') as f:
    data = f.read()

print(f"Block size: {len(data)}")

# Search for uasset magic (0x00000000) followed by valid version
pos = 0
while True:
    pos = data.find(b'\x00\x00\x00\x00', pos)
    if pos < 0:
        break
    if pos + 8 <= len(data):
        version = struct.unpack('<I', data[pos+4:pos+8])[0]
        # UE4 versions are typically 200-1000+
        if 100 <= version <= 2000:
            print(f"Found potential uasset at 0x{pos:x}: version={version}")
            # Try to parse package summary
            if pos + 100 <= len(data):
                # Package summary has: magic(4) + version(4) + package_version(4) + ...
                pkg_ver = struct.unpack('<I', data[pos+8:pos+12])[0]
                print(f"  Package version: {pkg_ver}")
                # Name count at offset ~0x20-0x30
    pos += 4

# Also search for legacy package magic 0x9E2A83C1 (C1 83 2A 9E little endian)
pos = 0
while True:
    pos = data.find(b'\xc1\x83\x2a\x9e', pos)
    if pos < 0:
        break
    print(f"Found legacy package magic at 0x{pos:x}")
    pos += 4

