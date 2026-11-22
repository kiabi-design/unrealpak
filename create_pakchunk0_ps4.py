#!/usr/bin/env python3
"""
Create PS4 pakchunk0 files from PC GameVoice mod asset registry.
Creates:
- pakchunk0-ps4.pak (UE4 pak v11)
- pakchunk0-ps4.utoc (IoStore table of contents)
- pakchunk0-ps4.ucas (IoStore container)
"""

import os
import struct
import hashlib
from pathlib import Path

# PS4 container ID (from pakchunk2)
CONTAINER_ID = bytes.fromhex('c12719ab10631d4b')

# Paths
PC_UCAS_9 = "/home/user/Desktop/game-voice/extracted_PC/Paks/pakchunk0-WindowsNoEditor_9-GV-RU_P.ucas"
OUTPUT_DIR = "/home/user/Desktop/game-voice/ps4_pakchunk0_output"

PAK_OUTPUT = os.path.join(OUTPUT_DIR, "pakchunk0-ps4.pak")
UTOC_OUTPUT = os.path.join(OUTPUT_DIR, "pakchunk0-ps4.utoc")
UCAS_OUTPUT = os.path.join(OUTPUT_DIR, "pakchunk0-ps4.ucas")

# UE4 Pak v11 constants
PAK_MAGIC = 0x5A6F12E1
PAK_VERSION = 11

def sha1_hash(data):
    return hashlib.sha1(data).digest()

def extract_asset_registry(ucas_path):
    """Extract asset paths from 9-GV-RU_P UCAS."""
    with open(ucas_path, 'rb') as f:
        data = f.read()

    strings = []
    pos = 0x40  # Skip header
    while pos < len(data):
        if data[pos] == 0:
            pos += 1
            continue
        end = data.find(b'\x00', pos)
        if end < 0:
            break
        s = data[pos:end]
        if len(s) > 3:
            try:
                decoded = s.decode('utf-8')
                # Asset paths have a 1-char prefix, then /Game/ or /Script/
                if len(decoded) > 1 and (decoded[1:].startswith('/Game/') or decoded[1:].startswith('/Script/')):
                    strings.append(decoded[1:])  # Strip prefix
            except:
                pass
        pos = end + 1

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for s in strings:
        if s not in seen:
            seen.add(s)
            unique.append(s)

    return unique

def create_pak_file(asset_paths, output_path):
    """Create UE4 pak v11 file with asset entries."""
    print(f"Creating pak with {len(asset_paths)} entries...")

    # Sort for consistent ordering
    asset_paths = sorted(asset_paths)

    # For each asset, create a placeholder entry
    # In reality, these would be actual .uasset files
    # We'll create minimal valid uasset-like data for each
    file_data = []
    current_offset = 0

    for i, asset_path in enumerate(asset_paths):
        # Create minimal uasset placeholder
        # UE4 asset files have a specific format, but for placeholder we use minimal data
        # Format: package header + name map + export table + import table + data
        # For simplicity, create a small binary blob with the asset path embedded

        # Minimal package header (simplified)
        placeholder = bytearray()
        placeholder.extend(b'\x00' * 4)  # Package file tag
        placeholder.extend(struct.pack('<I', 0x4D455441))  # 'META' tag
        placeholder.extend(struct.pack('<I', 0))  # Version
        placeholder.extend(struct.pack('<I', len(asset_path) + 1))
        placeholder.extend(asset_path.encode('utf-8') + b'\x00')
        placeholder.extend(b'\x00' * 16)  # Padding

        size = len(placeholder)
        file_hash = sha1_hash(placeholder)

        file_data.append({
            'name': asset_path.replace('/', '_').replace('.', '_') + '.uasset',
            'original_path': asset_path,
            'offset': current_offset,
            'size': size,
            'hash': file_hash,
            'data': placeholder
        })

        current_offset += size

        if (i + 1) % 1000 == 0:
            print(f"  Processed {i+1}/{len(asset_paths)} entries...")

    print(f"Total data size: {current_offset} bytes ({current_offset/1024/1024:.1f} MB)")

    # Build index
    print("Building index...")
    index_data = bytearray()
    for entry in file_data:
        # Name (null-terminated UTF-8)
        name_bytes = entry['name'].encode('utf-8') + b'\x00'
        index_data.extend(name_bytes)

        # Offset (uint64)
        index_data.extend(struct.pack('<Q', entry['offset']))

        # Size (uint64)
        index_data.extend(struct.pack('<Q', entry['size']))

        # Hash (20 bytes SHA1)
        index_data.extend(entry['hash'])

        # Compression method (uint32) - 0 = none
        index_data.extend(struct.pack('<I', 0))

        # Compressed size (uint64) - same as size
        index_data.extend(struct.pack('<Q', entry['size']))

        # Encrypted flag (uint8) - 0 = not encrypted
        index_data.extend(b'\x00')

    index_size = len(index_data)
    print(f"Index size: {index_size} bytes ({index_size/1024/1024:.1f} MB)")

    # Write pak file
    print("Writing pak file...")
    with open(output_path, 'wb') as pak:
        # Write file data
        for entry in file_data:
            pak.write(entry['data'])

        # Write index
        index_offset = pak.tell()
        pak.write(index_data)

        # Write footer (matching PS4 pakchunk2 format - 204 bytes)
        index_hash = sha1_hash(index_data)

        footer = bytearray()
        footer.extend(struct.pack('<I', PAK_MAGIC))      # Magic (4)
        footer.extend(struct.pack('<i', PAK_VERSION))    # Version (4)
        footer.extend(struct.pack('<q', index_offset))   # IndexOffset (8)
        footer.extend(struct.pack('<q', index_size))     # IndexSize (8)
        footer.extend(index_hash)                         # IndexHash (20)
        footer.extend(b'\x00' * 16)                       # EncryptionGUID (16)
        # Total so far: 60 bytes

        # Pad to 204 bytes (matching original PS4 pakchunk2)
        footer.extend(b'\x00' * (204 - len(footer)))

        pak.write(footer)

        total_size = pak.tell()
        print(f"Pak file size: {total_size} bytes ({total_size/1024/1024:.1f} MB)")

    return file_data

def create_utoc_file(output_path, pak_size):
    """Create minimal IoStore UTOC file (like PS4 pakchunk2.utoc)."""
    print("Creating UTOC...")

    # PS4 pakchunk2.utoc structure:
    # Magic (16) + Version (4) + HeaderSize (4) + EntryCount (4) + EntrySize (4)
    # + CBCount (4) + CBEntrySize (4) + ContainerInfo (32) + Entry (16) + CBEntries (96) + DirectoryIndex

    utoc = bytearray()

    # Magic
    utoc.extend(b'-==--==--==--==-')  # 16 bytes

    # Version 3 (PS4 uses version 3)
    utoc.extend(struct.pack('<I', 3))

    # Header size: 144 (0x90)
    utoc.extend(struct.pack('<I', 144))

    # Entry count: 1 (single container entry)
    utoc.extend(struct.pack('<I', 1))

    # Entry size: 16 (two uint64: container_id + size/flags)
    utoc.extend(struct.pack('<I', 16))

    # Compressed block count: 12
    utoc.extend(struct.pack('<I', 12))

    # Compressed block entry size: 8
    utoc.extend(struct.pack('<I', 8))

    # Container info (32 bytes at 0x28-0x47)
    # Container ID
    utoc.extend(CONTAINER_ID)  # 8 bytes
    utoc.extend(b'\x00' * 8)   # 8 bytes padding
    utoc.extend(struct.pack('<I', 8))  # 4 bytes
    utoc.extend(b'\x00' * 4)   # 4 bytes padding
    utoc.extend(b'\x08\x00\x00\x00\x00\x00\x00\x00')  # 8 bytes
    utoc.extend(b'\xff\xff\xff\xff\xff\xff\xff\xff')  # 8 bytes
    # Total 40 bytes from 0x28, but we need to reach 0x90 (144)

    # Pad to header_size (144)
    while len(utoc) < 144:
        utoc.extend(b'\x00')

    # Entry at offset 144 (header_size): 16 bytes
    # Container ID + size/flags
    utoc.extend(CONTAINER_ID)  # 8 bytes
    utoc.extend(struct.pack('<Q', 0x0A000000))  # 8 bytes (size/flags like PS4)

    # Compressed block entries (12 * 8 = 96 bytes)
    # Based on PS4 pakchunk2.utoc CB entries
    cb_entries = [
        b'\x00\x00\x00\x00\x00\x00\x00\x00',
        b'\x00\x2c\x00\x00\x01\x00\x00\x00',
        b'\x00\x07\x35\x65\x00\x00\x09\x00',
        b'\x00\x00\x00\x02\x1c\x57\x00\x00',
        b'\x00\x00\x00\x2e\x00\x00\x2c\x00',
        b'\x00\x01\x30\x00\x00\x00\x00\x0f',
        b'\x71\x00\x00\x00\x01\x01\x40\x71',
        b'\x00\x00\x00\x3e\x2f\x00\x00\x00',
        b'\x01\x01\x80\xa0\x00\x00\x00\xc8',
        b'\x22\x00\x00\x00\x01\x01\x50\xc3',
        b'\x00\x00\x00\x2f\x20\x00\x00\x00',
        b'\x01\x01\x80\xe3\x00\x00\x00\x1a',
    ]
    for cb in cb_entries:
        utoc.extend(cb)

    # Oodle string and padding (like PS4)
    utoc.extend(b'Oodle\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')

    # Directory index (simplified)
    # PS4 has: ../../../ path and some index data
    utoc.extend(b'../../../\x00')
    utoc.extend(b'\x00' * 7)

    # Add some index entries (like PS4)
    for i in range(8):
        utoc.extend(struct.pack('<I', i))
        utoc.extend(b'\xff\xff\xff\xff')

    # Final padding
    while len(utoc) < 245:  # PS4 pakchunk2.utoc is 245 bytes
        utoc.extend(b'\x00')

    with open(output_path, 'wb') as f:
        f.write(utoc)

    print(f"UTOC size: {len(utoc)} bytes")

def create_ucas_file(output_path):
    """Create minimal IoStore UCAS file (like PS4 pakchunk2.ucas)."""
    print("Creating UCAS...")

    # PS4 pakchunk2.ucas structure (48 bytes):
    # Container ID (8) + offset/size (8) + padding (16) + Container ID (8) + padding (8)

    ucas = bytearray()

    # Container header
    ucas.extend(CONTAINER_ID)  # 8 bytes
    ucas.extend(struct.pack('<Q', 0xC164000000000000))  # 8 bytes (offset/size like PS4)
    ucas.extend(b'\x00' * 16)  # 16 bytes padding
    ucas.extend(CONTAINER_ID)  # 8 bytes
    ucas.extend(b'\x00' * 8)   # 8 bytes padding

    # Total 48 bytes like PS4
    with open(output_path, 'wb') as f:
        f.write(ucas)

    print(f"UCAS size: {len(ucas)} bytes")

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("CREATING PS4 PAKCHUNK0 FROM PC GAMEVOICE MOD")
    print("=" * 60)

    # Extract asset registry from PC mod
    print("\n1. Extracting asset registry from 9-GV-RU_P UCAS...")
    asset_paths = extract_asset_registry(PC_UCAS_9)
    print(f"   Found {len(asset_paths)} unique asset paths")

    # Filter for GameVoice-related assets (SwGame, Narrative, UI, Audio)
    gv_assets = [p for p in asset_paths if any(kw in p for kw in
        ['SwGame', 'Narrative', 'UI_', 'Audio', 'Font', 'Localised', 'Dialogue', 'Voice', 'Caption', 'Subtitle'])]
    print(f"   GameVoice-related assets: {len(gv_assets)}")

    # Use all assets for completeness (user wants ALL)
    all_assets = asset_paths
    print(f"   Using all {len(all_assets)} assets for pakchunk0")

    # Create pak file
    print("\n2. Creating UE4 pak v11 file...")
    file_data = create_pak_file(all_assets, PAK_OUTPUT)

    # Get pak size for UTOC
    pak_size = os.path.getsize(PAK_OUTPUT)

    # Create UTOC
    print("\n3. Creating UTOC...")
    create_utoc_file(UTOC_OUTPUT, pak_size)

    # Create UCAS
    print("\n4. Creating UCAS...")
    create_ucas_file(UCAS_OUTPUT)

    print("\n" + "=" * 60)
    print("DONE!")
    print(f"Pak:  {PAK_OUTPUT}")
    print(f"UTOC: {UTOC_OUTPUT}")
    print(f"UCAS: {UCAS_OUTPUT}")
    print("=" * 60)

    # Verify
    print("\nVerifying...")
    for path in [PAK_OUTPUT, UTOC_OUTPUT, UCAS_OUTPUT]:
        size = os.path.getsize(path)
        print(f"  {os.path.basename(path)}: {size} bytes")

if __name__ == '__main__':
    main()