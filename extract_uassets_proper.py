#!/usr/bin/env python3
"""
Extract .uasset files from 9-GV-RU_P UCAS/UTOC
"""

import os
import struct
import sys

def parse_utoc(utoc_path):
    """Parse IoStore UTOC file."""
    with open(utoc_path, 'rb') as f:
        data = f.read()

    magic = data[:16]
    version = struct.unpack('<I', data[16:20])[0]
    header_size = struct.unpack('<I', data[20:24])[0]
    entry_count = struct.unpack('<I', data[24:28])[0]
    entry_size = struct.unpack('<I', data[28:32])[0]
    cb_count = struct.unpack('<I', data[32:36])[0]
    cb_entry_size = struct.unpack('<I', data[36:40])[0]

    print(f"UTOC: version={version}, header_size={header_size}")
    print(f"Entries: {entry_count} (size={entry_size}), CB: {cb_count} (size={cb_entry_size})")

    # Parse entries - each is 24 bytes in v2 (name_hash[20] + offset[8] or similar)
    entries = []
    for i in range(entry_count):
        offset = header_size + i * entry_size
        entry_data = data[offset:offset+entry_size]
        if len(entry_data) >= 24:
            name_hash = entry_data[:20]
            # Entry structure: 20 byte hash + 8 byte offset (or 4+4)
            # Let's check based on remaining data
            off = struct.unpack('<Q', entry_data[20:28])[0] if len(entry_data) >= 28 else 0
            sz = struct.unpack('<I', entry_data[28:32])[0] if len(entry_data) >= 32 else 0
            entries.append({'name_hash': name_hash, 'offset': off, 'size': sz, 'raw': entry_data})
            print(f"  Entry {i}: hash={name_hash.hex()}, offset=0x{off:x}, size=0x{sz:x}")

    # Parse compressed block entries
    cb_start = header_size + entry_count * entry_size
    cb_entries = []
    for i in range(cb_count):
        offset = cb_start + i * cb_entry_size
        if offset + 8 <= len(data):
            cb_data = data[offset:offset+8]
            cb_off = struct.unpack('<I', cb_data[:4])[0]
            cb_sz = struct.unpack('<I', cb_data[4:8])[0]
            cb_entries.append({'offset': cb_off, 'size': cb_sz})
            print(f"  CB {i}: offset=0x{cb_off:x}, size=0x{cb_sz:x}")

    return {
        'version': version,
        'header_size': header_size,
        'entry_count': entry_count,
        'entry_size': entry_size,
        'entries': entries,
        'cb_count': cb_count,
        'cb_entry_size': cb_entry_size,
        'cb_entries': cb_entries,
        'container_id': data[0x30:0x38],
        'raw': data
    }

def parse_utoc_full(utoc_path):
    """Parse full UTOC including string table for paths"""
    with open(utoc_path, 'rb') as f:
        data = f.read()

    magic = data[:16]
    version = struct.unpack('<I', data[16:20])[0]
    header_size = struct.unpack('<I', data[20:24])[0]
    entry_count = struct.unpack('<I', data[24:28])[0]
    entry_size = struct.unpack('<I', data[28:32])[0]
    cb_count = struct.unpack('<I', data[32:36])[0]
    cb_entry_size = struct.unpack('<I', data[36:40])[0]
    string_table_offset = struct.unpack('<Q', data[40:48])[0] if len(data) >= 48 else 0
    string_table_size = struct.unpack('<I', data[48:52])[0] if len(data) >= 52 else 0

    print(f"String table: offset=0x{string_table_offset:x}, size={string_table_size}")

    # Parse entries - in UE5 IoStore v2, entry is 24 bytes: 20 byte name hash + 4 byte offset + 4 byte size (or 8+4)
    entries = []
    for i in range(entry_count):
        offset = header_size + i * entry_size
        entry_data = data[offset:offset+entry_size]
        if len(entry_data) >= 24:
            name_hash = entry_data[:20]
            # Try different parsing
            if entry_size >= 28:
                off = struct.unpack('<Q', entry_data[20:28])[0]
                sz = struct.unpack('<I', entry_data[28:32])[0] if entry_size >= 32 else 0
            else:
                off = struct.unpack('<I', entry_data[20:24])[0]
                sz = struct.unpack('<I', entry_data[24:28])[0]
            entries.append({'name_hash': name_hash, 'offset': off, 'size': sz, 'index': i})

    # Read string table
    string_table = ""
    if string_table_offset > 0 and string_table_size > 0 and string_table_offset < len(data):
        string_table = data[string_table_offset:string_table_offset+string_table_size].decode('utf-8', errors='ignore')
        print(f"String table content (first 500): {string_table[:500]}")

    return {
        'entries': entries,
        'cb_entries': [],  # We'll parse CB differently
        'string_table': string_table,
        'raw': data
    }

def extract_from_ucas(ucas_path, entries, output_dir):
    """Extract uasset files from UCAS using entry offsets"""
    os.makedirs(output_dir, exist_ok=True)
    
    with open(ucas_path, 'rb') as f:
        ucas_data = f.read()
    
    print(f"UCAS size: {len(ucas_data)} bytes")
    
    # The UCAS seems to contain concatenated asset data
    # Let's find the actual asset boundaries by looking for uasset headers
    for entry in entries:
        off = entry['offset']
        sz = entry['size']
        if off >= len(ucas_data) or sz == 0:
            continue
        asset_data = ucas_data[off:off+sz]
        if len(asset_data) < 4:
            continue
        
        # Check for uasset magic (0x00000000) or other signatures
        if asset_data[:4] == b'\x00\x00\x00\x00':
            # This is a uasset - find its actual size by looking for next asset or end
            out_path = os.path.join(output_dir, f"asset_{entry['index']}.uasset")
            with open(out_path, 'wb') as f:
                f.write(asset_data)
            print(f"  Extracted asset_{entry['index']}.uasset ({len(asset_data)} bytes) at offset 0x{off:x}")
        elif asset_data[:4] == b'BKHD':
            out_path = os.path.join(output_dir, f"asset_{entry['index']}.bnk")
            with open(out_path, 'wb') as f:
                f.write(asset_data)
            print(f"  Extracted asset_{entry['index']}.bnk ({len(asset_data)} bytes) at offset 0x{off:x}")

def find_uassets_in_ucas(ucas_path, output_dir):
    """Scan UCAS for uasset packages directly"""
    os.makedirs(output_dir, exist_ok=True)
    
    with open(ucas_path, 'rb') as f:
        data = f.read()
    
    print(f"Scanning UCAS ({len(data)} bytes) for uasset packages...")
    
    # Find all package headers (0x00000000)
    pos = 0
    count = 0
    while True:
        pos = data.find(b'\x00\x00\x00\x00', pos)
        if pos < 0:
            break
        # Check if this looks like a valid package header
        # Package header: 4 byte magic + 4 byte version + 4 byte license + ...
        if pos + 20 < len(data):
            # Try to determine package size by finding next header or reasonable max
            # For now, extract a chunk
            chunk_size = min(500000, len(data) - pos)
            chunk = data[pos:pos+chunk_size]
            out_path = os.path.join(output_dir, f"uasset_{pos:08x}.uasset")
            with open(out_path, 'wb') as f:
                f.write(chunk)
            print(f"  Found uasset at 0x{pos:x} -> {out_path} ({chunk_size} bytes)")
            count += 1
        pos += 4
    
    print(f"Total uassets found: {count}")
    return count

def main():
    base = "/home/user/Desktop/game-voice/extracted_PC/Paks"
    output_dir = "/tmp/pakchunk0_extracted/uassets"
    
    # Parse 9-GV-RU_P UTOC
    print("="*60)
    print("PARSING 9-GV-RU_P UTOC")
    print("="*60)
    utoc_info = parse_utoc(f"{base}/pakchunk0-WindowsNoEditor_9-GV-RU_P.utoc")
    
    # Also try full parse with string table
    print("\n" + "="*60)
    print("FULL UTOC PARSE")
    print("="*60)
    full_info = parse_utoc_full(f"{base}/pakchunk0-WindowsNoEditor_9-GV-RU_P.utoc")
    
    # Extract from UCAS using entry offsets
    print("\n" + "="*60)
    print("EXTRACTING FROM UCAS (entry offsets)")
    print("="*60)
    extract_from_ucas(
        f"{base}/pakchunk0-WindowsNoEditor_9-GV-RU_P.ucas",
        utoc_info['entries'],
        f"{output_dir}/from_entries"
    )
    
    # Also scan UCAS directly for uasset packages
    print("\n" + "="*60)
    print("SCANNING UCAS FOR UASSET PACKAGES")
    print("="*60)
    find_uassets_in_ucas(
        f"{base}/pakchunk0-WindowsNoEditor_9-GV-RU_P.ucas",
        f"{output_dir}/scanned"
    )

if __name__ == '__main__':
    main()
