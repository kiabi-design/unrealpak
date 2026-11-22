#!/usr/bin/env python3
"""
Extract files from UE5 IoStore format (PC GameVoice pakchunk0).
"""

import struct
import os
import hashlib

class IoStoreExtractor:
    def __init__(self, utoc_path, ucas_path):
        with open(utoc_path, 'rb') as f:
            self.utoc = f.read()
        with open(ucas_path, 'rb') as f:
            self.ucas = f.read()

        self.parse_header()
        self.parse_entries()
        self.parse_compressed_blocks()
        self.parse_name_table()

    def parse_header(self):
        # Magic at 0x00 (16 bytes)
        self.magic = self.utoc[0:16]
        # Version at 0x10
        self.version = struct.unpack('<I', self.utoc[0x10:0x14])[0]
        # Header size at 0x14
        self.header_size = struct.unpack('<I', self.utoc[0x14:0x18])[0]
        # Entry count at 0x18
        self.entry_count = struct.unpack('<I', self.utoc[0x18:0x1C])[0]
        # Entry size at 0x1C
        self.entry_size = struct.unpack('<I', self.utoc[0x1C:0x20])[0]
        # Compressed block count at 0x20
        self.cb_count = struct.unpack('<I', self.utoc[0x20:0x24])[0]
        # Compressed block entry size at 0x24
        self.cb_entry_size = struct.unpack('<I', self.utoc[0x24:0x28])[0]

        print(f"Magic: {self.magic}")
        print(f"Version: {self.version}")
        print(f"Header size: {self.header_size}")
        print(f"Entry count: {self.entry_count}, Entry size: {self.entry_size}")
        print(f"CB count: {self.cb_count}, CB entry size: {self.cb_entry_size}")

    def parse_entries(self):
        self.entries = []
        for i in range(self.entry_count):
            offset = self.header_size + i * self.entry_size
            entry_data = self.utoc[offset:offset+self.entry_size]

            # Standard UE5 IoStore entry format (17 bytes for this version):
            # Offset (8 bytes) - offset in UCAS
            # Size (8 bytes) - uncompressed size
            # Compression method (1 byte)
            if len(entry_data) >= 17:
                offset_val = struct.unpack('<Q', entry_data[0:8])[0]
                size = struct.unpack('<Q', entry_data[8:16])[0]
                comp_method = entry_data[16]
                self.entries.append({
                    'index': i,
                    'offset': offset_val,
                    'size': size,
                    'comp_method': comp_method,
                    'raw': entry_data
                })
                print(f"  Entry {i}: offset={offset_val}, size={size}, comp={comp_method}")
            else:
                print(f"  Entry {i}: too small ({len(entry_data)} bytes): {entry_data.hex()}")

    def parse_compressed_blocks(self):
        self.cb_entries = []
        cb_start = 0x28
        # The CB entries seem to start right after the fixed header (0x28)
        # But in the hex dump, entries start at 0x90 (header_size)
        # And CB entries are between 0xA0 and 0x1A0
        # Let's find them

        # Actually, looking at the hex dump:
        # 0x90-0xA0: 3 entries × 17 bytes = 51 bytes (0x90-0xC3)
        # 0xC0-0x1A0: compressed block entries (12 blocks)
        # 0x1A0+: name table

        cb_start = self.header_size + self.entry_count * self.entry_size
        print(f"CB entries start at offset 0x{cb_start:x}")

        for i in range(self.cb_count):
            offset = cb_start + i * self.cb_entry_size
            if self.cb_entry_size == 0:
                # Variable size - need to parse differently
                break
            cb_data = self.utoc[offset:offset+self.cb_entry_size]
            self.cb_entries.append(cb_data)

    def parse_name_table(self):
        # Find the string table after CB entries
        # In the hex dump, it starts around 0x1A0
        cb_end = 0x28 + self.cb_count * self.cb_entry_size if self.cb_entry_size > 0 else self.header_size + self.entry_count * self.entry_size + 100

        # Search for the string table pattern: null-terminated strings
        # Starting from 0x1A0 in the hex dump
        self.name_table_offset = 0x1A0
        self.names = []

        pos = self.name_table_offset
        while pos < len(self.utoc):
            # Read null-terminated string
            end = self.utoc.find(b'\x00', pos)
            if end < 0 or end == pos:
                pos += 1
                continue
            name = self.utoc[pos:end].decode('utf-8', errors='ignore')
            if name and len(name) > 1:
                self.names.append((pos, name))
            pos = end + 1
            if pos > len(self.utoc) - 10:
                break

        print(f"Found {len(self.names)} names in string table")
        for offset, name in self.names[:20]:
            print(f"  0x{offset:x}: {name}")

    def extract_files(self, output_dir):
        os.makedirs(output_dir, exist_ok=True)

        # The entries point to data in UCAS
        # But the entry format might be different - let's check
        # Entry 0: offset=0xF597ADF4FC84F2A6 (huge), size=0x7CDADF9202000000 (huge)
        # These are clearly not direct UCAS offsets

        # In UE5 IoStore, the entries contain:
        # - Offset: block index into compressed blocks
        # - Size: uncompressed size
        # The actual data is in compressed blocks

        # Let's look at the compressed block entries
        # They're at offset 0xA0-0x1A0 in the hex dump
        # Each seems to be 16 bytes: offset(8) + size(8) or similar

        print("\nAnalyzing compressed block entries...")
        cb_start = 0xA0  # From hex dump
        for i in range(self.cb_count):
            offset = cb_start + i * 16  # Guessing 16 bytes per CB entry
            if offset + 16 <= len(self.utoc):
                cb = self.utoc[offset:offset+16]
                cb_offset = struct.unpack('<Q', cb[0:8])[0]
                cb_size = struct.unpack('<Q', cb[8:16])[0]
                print(f"  CB {i}: offset=0x{cb_offset:x} ({cb_offset}), size=0x{cb_size:x} ({cb_size})")
                if cb_offset < len(self.ucas) and cb_offset + cb_size <= len(self.ucas):
                    data = self.ucas[cb_offset:cb_offset+cb_size]
                    print(f"    Data preview: {data[:50].hex()}")

        # The UCAS data is likely compressed with the blocks
        # This is getting complex. Let's try a different approach.

        # For now, let's just save the UCAS as a single file for analysis
        with open(os.path.join(output_dir, 'full_ucas.bin'), 'wb') as f:
            f.write(self.ucas)
        print(f"\nSaved full UCAS to {output_dir}/full_ucas.bin")

def main():
    for suffix in ['8-GV-RU_P', '9-GV-RU_P']:
        print(f"\n{'='*60}")
        print(f"PROCESSING {suffix}")
        print(f"{'='*60}")

        utoc_path = f'/home/user/Desktop/game-voice/extracted_PC/Paks/pakchunk0-WindowsNoEditor_{suffix}.utoc'
        ucas_path = f'/home/user/Desktop/game-voice/extracted_PC/Paks/pakchunk0-WindowsNoEditor_{suffix}.ucas'
        output_dir = f'/home/user/Desktop/game-voice/extracted_pakchunk0_{suffix}'

        extractor = IoStoreExtractor(utoc_path, ucas_path)
        extractor.extract_files(output_dir)

if __name__ == '__main__':
    main()