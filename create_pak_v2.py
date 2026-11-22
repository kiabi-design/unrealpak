#!/usr/bin/env python3
"""
Create UE4 pak file (v11) matching original footer format exactly.
"""

import os
import struct
import hashlib
from pathlib import Path

# Paths
EXTRACT_DIR = "/home/user/Desktop/game-voice/pak_extracted_full"
RESPONSE_FILE = "/home/user/Desktop/game-voice/pak_response.txt"
OUTPUT_PAK = "/home/user/Desktop/game-voice/pakchunk2-ps4_russian.pak"

# UE4 Pak v11 constants
PAK_MAGIC = 0x5A6F12E1
PAK_VERSION = 11

def sha1_hash(data):
    return hashlib.sha1(data).digest()

def read_response_file():
    """Parse response file to get file list."""
    entries = []
    with open(RESPONSE_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Format: "filename" "/path/to/file"
            parts = line.split('" "')
            if len(parts) == 2:
                name = parts[0][1:]  # Remove leading "
                path = parts[1][:-1]  # Remove trailing "
                entries.append((name, path))
    return entries

def create_pak():
    print("=" * 60)
    print("CREATING UE4 PAK FILE (v11) - CORRECTED FOOTER")
    print("=" * 60)

    entries = read_response_file()
    print(f"Total files: {len(entries)}")

    # Sort entries by name for consistent ordering
    entries.sort(key=lambda x: x[0])

    # First pass: collect file data and compute offsets/sizes/hashes
    file_data = []
    current_offset = 0

    print("Reading files and computing hashes...")
    for i, (name, path) in enumerate(entries):
        with open(path, 'rb') as f:
            data = f.read()

        size = len(data)
        file_hash = sha1_hash(data)

        file_data.append({
            'name': name,
            'offset': current_offset,
            'size': size,
            'hash': file_hash,
            'data': data
        })

        current_offset += size

        if (i + 1) % 5000 == 0:
            print(f"  Processed {i+1}/{len(entries)} files...")

    print(f"Total data size: {current_offset} bytes ({current_offset/1024/1024:.1f} MB)")

    # Build index (matching original format exactly)
    # For each file:
    #   - Name (null-terminated UTF-8 string)
    #   - Offset (uint64)
    #   - Size (uint64)
    #   - Hash (20 bytes SHA1)
    #   - Compression method (uint32) - 0 = none
    #   - Compressed size (uint64) - same as size if not compressed
    #   - Encryption flag (uint8) - 0 = not encrypted

    print("Building index...")
    index_data = bytearray()
    for entry in file_data:
        name_bytes = entry['name'].encode('utf-8') + b'\x00'
        index_data.extend(name_bytes)
        index_data.extend(struct.pack('<Q', entry['offset']))
        index_data.extend(struct.pack('<Q', entry['size']))
        index_data.extend(entry['hash'])
        index_data.extend(struct.pack('<I', 0))  # Compression method
        index_data.extend(struct.pack('<Q', entry['size']))  # Compressed size
        index_data.extend(b'\x00')  # Encrypted flag

    index_size = len(index_data)
    print(f"Index size: {index_size} bytes ({index_size/1024/1024:.1f} MB)")

    # Write pak file
    print("Writing pak file...")
    with open(OUTPUT_PAK, 'wb') as pak:
        # Write file data
        for entry in file_data:
            pak.write(entry['data'])

        # Write index
        index_offset = pak.tell()
        pak.write(index_data)

        # Write footer (matching original exactly - 44 bytes minimum + padding to 204?)
        # Original footer structure:
        # Magic (4) + Version (4) + IndexOffset (8) + IndexSize (8) + IndexHash (20) + EncryptionGUID (16) = 60 bytes
        # Then padding to 204 bytes total

        index_hash = sha1_hash(index_data)

        footer = bytearray()
        footer.extend(struct.pack('<I', PAK_MAGIC))      # Magic (4)
        footer.extend(struct.pack('<i', PAK_VERSION))    # Version (4)
        footer.extend(struct.pack('<q', index_offset))   # IndexOffset (8)
        footer.extend(struct.pack('<q', index_size))     # IndexSize (8)
        footer.extend(index_hash)                         # IndexHash (20)
        footer.extend(b'\x00' * 16)                       # EncryptionGUID (16)
        # Total so far: 60 bytes

        # Pad to 204 bytes (matching original)
        footer.extend(b'\x00' * (204 - len(footer)))

        pak.write(footer)

        total_size = pak.tell()
        print(f"Pak file size: {total_size} bytes ({total_size/1024/1024:.1f} MB)")

    print(f"\nPak created: {OUTPUT_PAK}")
    return True

def verify_pak():
    """Verify the created pak matches original format."""
    print("\nVerifying pak...")
    with open(OUTPUT_PAK, 'rb') as f:
        f.seek(-204, 2)
        data = f.read(204)

        magic = struct.unpack('<I', data[0:4])[0]
        version = struct.unpack('<i', data[4:8])[0]
        index_offset = struct.unpack('<q', data[8:16])[0]
        index_size = struct.unpack('<q', data[16:24])[0]
        index_hash = data[24:44]
        encryption_guid = data[44:60]

        print(f"Magic: {magic:#x} ({'OK' if magic == PAK_MAGIC else 'FAIL'})")
        print(f"Version: {version} ({'OK' if version == PAK_VERSION else 'FAIL'})")
        print(f"IndexOffset: {index_offset}")
        print(f"IndexSize: {index_size}")
        print(f"IndexHash: {index_hash.hex()}")
        print(f"EncryptionGUID: {encryption_guid.hex()}")

        # Verify index hash
        f.seek(index_offset)
        index_data = f.read(index_size)
        computed_hash = sha1_hash(index_data)
        print(f"Computed IndexHash: {computed_hash.hex()}")
        print(f"Index Hash Match: {'OK' if computed_hash == index_hash else 'FAIL'}")

        # Verify a few file entries
        print("\nVerifying index entries...")
        f.seek(index_offset)
        for i in range(min(5, 60343)):
            # Read null-terminated name
            name_bytes = bytearray()
            while True:
                b = f.read(1)
                if b == b'\x00' or not b:
                    break
                name_bytes.extend(b)
            name = name_bytes.decode('utf-8')
            offset = struct.unpack('<Q', f.read(8))[0]
            size = struct.unpack('<Q', f.read(8))[0]
            f.read(20)  # hash
            f.read(4)   # compression
            f.read(8)   # compressed size
            f.read(1)   # encrypted
            print(f"  [{i}] {name}: offset={offset}, size={size}")

if __name__ == '__main__':
    create_pak()
    verify_pak()