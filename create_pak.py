#!/usr/bin/env python3
"""
Create UE4 pak file (v11) from extracted files.
Pak format:
- File data (concatenated)
- Index (encrypted or plaintext)
- Footer (44 bytes for v11)
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
INDEX_ENCRYPTION = 0  # No encryption (plaintext index)
COMPRESSION_METHOD = 0  # No compression (Zlib = 1)

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
    print("CREATING UE4 PAK FILE (v11)")
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

    # Build index
    # Index format for v11 (plaintext):
    # For each file:
    #   - Name (null-terminated UTF-8 string)
    #   - Offset (uint64)
    #   - Size (uint64)
    #   - Hash (20 bytes SHA1)
    #   - Compression method (uint32)
    #   - Compressed size (uint64) - same as size if not compressed
    #   - Encryption flag (uint8)

    print("Building index...")
    index_data = bytearray()
    for entry in file_data:
        # Name (null-terminated)
        name_bytes = entry['name'].encode('utf-8') + b'\x00'
        index_data.extend(name_bytes)

        # Offset (uint64)
        index_data.extend(struct.pack('<Q', entry['offset']))

        # Size (uint64)
        index_data.extend(struct.pack('<Q', entry['size']))

        # Hash (20 bytes)
        index_data.extend(entry['hash'])

        # Compression method (uint32) - 0 = none
        index_data.extend(struct.pack('<I', COMPRESSION_METHOD))

        # Compressed size (uint64)
        index_data.extend(struct.pack('<Q', entry['size']))

        # Encryption flag (uint8) - 0 = not encrypted
        index_data.extend(b'\x00')

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

        # Write footer (v11 format)
        # struct FPakInfo
        #   Magic (uint32) = 0x5A6F12E1
        #   Version (int32) = 11
        #   IndexOffset (int64)
        #   IndexSize (int64)
        #   IndexHash (20 bytes SHA1)
        #   IndexEncryptionKeyGuid (16 bytes) - all zeros if not encrypted
        #   FooterSize (uint32) - size of this footer struct
        #   Additional fields for v11+

        index_hash = sha1_hash(index_data)

        # Footer for v11 (44 bytes minimum + extra fields)
        footer = bytearray()
        footer.extend(struct.pack('<I', PAK_MAGIC))      # Magic
        footer.extend(struct.pack('<i', PAK_VERSION))    # Version
        footer.extend(struct.pack('<q', index_offset))   # IndexOffset
        footer.extend(struct.pack('<q', index_size))     # IndexSize
        footer.extend(index_hash)                         # IndexHash (20 bytes)
        footer.extend(b'\x00' * 16)                       # IndexEncryptionKeyGuid (16 bytes)

        # For v11+, additional fields:
        footer.extend(struct.pack('<I', len(footer) + 4)) # FooterSize (including this field)
        footer.extend(b'\x00')                            # IndexEncryption (0 = none)
        footer.extend(struct.pack('<I', 0))               # IndexCompressionMethod (0 = none)
        footer.extend(struct.pack('<Q', index_size))      # CompressedIndexSize
        footer.extend(b'\x00' * 32)                       # Reserved/padding

        pak.write(footer)

        # Verify total size
        total_size = pak.tell()
        print(f"Pak file size: {total_size} bytes ({total_size/1024/1024:.1f} MB)")

    print(f"\nPak created: {OUTPUT_PAK}")
    return True

def verify_pak():
    """Verify the created pak can be read."""
    print("\nVerifying pak...")
    with open(OUTPUT_PAK, 'rb') as f:
        # Read footer from end
        f.seek(-44, 2)  # Minimum footer size
        magic = struct.unpack('<I', f.read(4))[0]
        if magic == PAK_MAGIC:
            print("  Magic: OK")
        else:
            # Try reading from different offset (footer might be larger)
            f.seek(-100, 2)
            data = f.read(100)
            idx = data.rfind(struct.pack('<I', PAK_MAGIC))
            if idx >= 0:
                f.seek(f.tell() - 100 + idx)
                magic = struct.unpack('<I', f.read(4))[0]
                version = struct.unpack('<i', f.read(4))[0]
                index_offset = struct.unpack('<q', f.read(8))[0]
                index_size = struct.unpack('<q', f.read(8))[0]
                print(f"  Magic: OK (found at offset {f.tell()-4})")
                print(f"  Version: {version}")
                print(f"  IndexOffset: {index_offset}")
                print(f"  IndexSize: {index_size}")
            else:
                print("  Magic: NOT FOUND")
                return False

    return True

if __name__ == '__main__':
    create_pak()
    verify_pak()