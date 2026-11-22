#!/usr/bin/env python3
"""
Extract PC pakchunk0 IoStore files and create PS4-format pak files.
"""

import struct
import os
import hashlib
import json

def parse_utoc(utoc_data):
    """Parse PS4-style UTOC."""
    if utoc_data[:4] != b'-==-':
        return None

    header_size = struct.unpack('<I', utoc_data[0x14:0x18])[0]
    entry_count = struct.unpack('<I', utoc_data[0x18:0x1C])[0]
    entry_size = struct.unpack('<I', utoc_data[0x1C:0x20])[0]
    cb_count = struct.unpack('<I', utoc_data[0x20:0x24])[0]
    cb_size = struct.unpack('<I', utoc_data[0x24:0x28])[0]

    entries = []
    for i in range(entry_count):
        entry_offset = header_size + i * entry_size
        if entry_offset + entry_size <= len(utoc_data):
            entry = utoc_data[entry_offset:entry_offset+entry_size]
            entries.append(entry)

    # Compressed block entries
    cb_entries = []
    cb_start = 0x28
    for i in range(cb_count):
        cb_offset = cb_start + i * cb_size
        if cb_offset + cb_size <= len(utoc_data):
            cb = utoc_data[cb_offset:cb_offset+cb_size]
            cb_entries.append(cb)

    return {
        'header_size': header_size,
        'entry_count': entry_count,
        'entry_size': entry_size,
        'cb_count': cb_count,
        'cb_size': cb_size,
        'entries': entries,
        'cb_entries': cb_entries
    }

def extract_iostore(pak_path, ucas_path, utoc_path, output_dir):
    """Extract files from IoStore format."""
    os.makedirs(output_dir, exist_ok=True)

    with open(utoc_path, 'rb') as f:
        utoc = f.read()

    with open(ucas_path, 'rb') as f:
        ucas = f.read()

    with open(pak_path, 'rb') as f:
        pak = f.read()

    parsed = parse_utoc(utoc)
    if not parsed:
        print(f"  Failed to parse UTOC")
        return []

    print(f"  UTOC parsed: {parsed['entry_count']} entries, {parsed['cb_count']} compressed blocks")
    print(f"  Entry size: {parsed['entry_size']}, CB size: {parsed['cb_size']}")

    # The entries are 12 or 17 bytes - very small
    # They might just be indexes into the UCAS
    # Let's look at the UCAS structure

    # For now, let's try to extract the UCAS as-is and see if it contains
    # recognizable file data

    extracted = []

    # The UCAS might be a concatenation of compressed blocks
    # Each compressed block entry (1 byte for 8-GV-RU_P) might indicate
    # compression method or block info

    # Let's just save the UCAS and PAK for analysis
    with open(os.path.join(output_dir, 'ucas_raw.bin'), 'wb') as f:
        f.write(ucas)
    with open(os.path.join(output_dir, 'pak_raw.bin'), 'wb') as f:
        f.write(pak)

    # Search for file boundaries in UCAS
    # Look for common file signatures
    signatures = {
        b'\x00\x00\x00\x00': 'empty',
        b'PK\x03\x04': 'zip',
        b'\x1f\x8b': 'gzip',
        b'BKHD': 'bnk',
        b'RIFF': 'riff',
        b'OggS': 'ogg',
        b'ID3': 'mp3',
        b'fLaC': 'flac',
        b'<?xml': 'xml',
        b'{' : 'json',
        b'[' : 'json_array',
    }

    print(f"  Scanning UCAS for file signatures...")
    for sig, name in signatures.items():
        pos = 0
        count = 0
        while True:
            pos = ucas.find(sig, pos)
            if pos < 0:
                break
            count += 1
            pos += 1
        if count > 0:
            print(f"    {name} ({sig}): {count} occurrences")

    # The UCAS for 9-GV-RU_P is 959KB - likely contains multiple files
    # Let's try to split by the compressed block entries

    return extracted

def main():
    print("=" * 60)
    print("EXTRACTING PC PAKCHUNK0 IOSTORE")
    print("=" * 60)

    for suffix in ['8-GV-RU_P', '9-GV-RU_P']:
        print(f"\n--- {suffix} ---")
        pak_path = f'extracted_PC/Paks/pakchunk0-WindowsNoEditor_{suffix}.pak'
        ucas_path = f'extracted_PC/Paks/pakchunk0-WindowsNoEditor_{suffix}.ucas'
        utoc_path = f'extracted_PC/Paks/pakchunk0-WindowsNoEditor_{suffix}.utoc'
        output_dir = f'extracted_pakchunk0_{suffix}'

        extract_iostore(pak_path, ucas_path, utoc_path, output_dir)

if __name__ == '__main__':
    main()