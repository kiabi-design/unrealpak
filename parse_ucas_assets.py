#!/usr/bin/env python3
"""
Parse 9-GV-RU_P UCAS to extract uasset files based on visible paths
"""

import os
import struct

with open('/home/user/Desktop/game-voice/extracted_PC/Paks/pakchunk0-WindowsNoEditor_9-GV-RU_P.ucas', 'rb') as f:
    data = f.read()

print(f"UCAS size: {len(data)} bytes")

# Find all asset paths in the UCAS
# Paths start with "/Game/" or "/Script/"
paths = []
pos = 0
while True:
    pos = data.find(b'/Game/', pos)
    if pos < 0:
        break
    # Find end of path (null terminator or .uasset)
    end = data.find(b'\x00', pos)
    if end < 0:
        end = pos + 200
    path = data[pos:end].decode('utf-8', errors='ignore')
    # Clean up
    if '.uasset' in path:
        path = path[:path.index('.uasset')+7]
    paths.append((pos, path))
    pos += 6

pos = 0
while True:
    pos = data.find(b'/Script/', pos)
    if pos < 0:
        break
    end = data.find(b'\x00', pos)
    if end < 0:
        end = pos + 200
    path = data[pos:end].decode('utf-8', errors='ignore')
    paths.append((pos, path))
    pos += 8

# Sort by position
paths.sort(key=lambda x: x[0])

print(f"\nFound {len(paths)} asset paths:")
for offset, path in paths:
    print(f"  0x{offset:08x}: {path}")

# Now try to extract assets between paths
# The format might be: [path]\0[asset_data][path]\0[asset_data]...
output_dir = '/tmp/extracted_uassets_ucas'
os.makedirs(output_dir, exist_ok=True)

for i, (offset, path) in enumerate(paths):
    # Find start of asset data (after null terminator)
    asset_start = data.find(b'\x00', offset)
    if asset_start < 0:
        asset_start = offset + len(path) + 1
    else:
        asset_start += 1
    
    # End is next path offset or end of file
    asset_end = paths[i+1][0] if i+1 < len(paths) else len(data)
    
    asset_data = data[asset_start:asset_end]
    
    # Check if it looks like a uasset
    if len(asset_data) > 4 and asset_data[:4] == b'\x00\x00\x00\x00':
        safe_name = path.replace('/', '_').replace('\\', '_').strip('_')
        out_path = os.path.join(output_dir, safe_name)
        with open(out_path, 'wb') as f:
            f.write(asset_data)
        print(f"Extracted: {safe_name} ({len(asset_data)} bytes)")

