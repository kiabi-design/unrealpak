import os
import struct

def extract_uassets_from_block(block_path, output_dir):
    """Extract uasset files from a decompressed Oodle block"""
    os.makedirs(output_dir, exist_ok=True)
    
    with open(block_path, 'rb') as f:
        data = f.read()
    
    print(f"Block size: {len(data)} bytes")
    
    # Find all uasset headers (0x00000000)
    # A uasset file starts with: 4 byte magic (0) + 4 byte version + ...
    pos = 0
    assets = []
    while True:
        pos = data.find(b'\x00\x00\x00\x00', pos)
        if pos < 0:
            break
        # Check if this looks like a valid uasset header
        if pos + 20 < len(data):
            # Read potential package header
            # Package header: magic(4) + version(4) + license(4) + ...
            version = struct.unpack('<I', data[pos+4:pos+8])[0]
            # UE4 package versions are typically around 500-1000
            if 100 <= version <= 2000:
                assets.append(pos)
                print(f"  Potential uasset at 0x{pos:x}, version={version}")
        pos += 4
    
    # Extract each asset (from one header to the next, or to end)
    for i, start in enumerate(assets):
        end = assets[i+1] if i+1 < len(assets) else len(data)
        asset_data = data[start:end]
        out_path = os.path.join(output_dir, f"asset_{i:03d}_0x{start:x}.uasset")
        with open(out_path, 'wb') as f:
            f.write(asset_data)
        print(f"    Extracted: {out_path} ({len(asset_data)} bytes)")

# Process block_006.bin
print("="*60)
print("Processing block_006.bin")
print("="*60)
extract_uassets_from_block(
    '/tmp/pakchunk0_extracted/8-GV-RU_P/block_006.bin',
    '/tmp/extracted_uassets/block_006'
)

print("\n" + "="*60)
print("Processing block_009.bin")
print("="*60)
extract_uassets_from_block(
    '/tmp/pakchunk0_extracted/8-GV-RU_P/block_009.bin',
    '/tmp/extracted_uassets/block_009'
)

