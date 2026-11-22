#!/usr/bin/env python3
"""
Extract 9-GV-RU_P from IoStore (UTOC/UCAS)
"""

import os
import struct
import ctypes
import sys

# Load Oodle library
OODLE_LIB_PATH = "/home/user/Desktop/game-voice/liboo2corelinux64.so.9"
try:
    OODLE_LIB = ctypes.CDLL(OODLE_LIB_PATH)
    print(f"Loaded Oodle library: {OODLE_LIB_PATH}")
except Exception as e:
    print(f"Failed to load Oodle library: {e}")
    sys.exit(1)

# OodleLZ_GetDecodeBufferSize
OodleLZ_GetDecodeBufferSize = OODLE_LIB.OodleLZ_GetDecodeBufferSize
OodleLZ_GetDecodeBufferSize.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
OodleLZ_GetDecodeBufferSize.restype = ctypes.c_size_t

# OodleLZ_Decompress
OodleLZ_Decompress = OODLE_LIB.OodleLZ_Decompress
OodleLZ_Decompress.argtypes = [
    ctypes.c_void_p,  # compBuf
    ctypes.c_size_t,  # compBufSize
    ctypes.c_void_p,  # rawBuf
    ctypes.c_size_t,  # rawLen
    ctypes.c_int,     # fuzzSafe
    ctypes.c_uint32,  # crc
    ctypes.c_int,     # verbose
    ctypes.c_void_p,  # dstBase
    ctypes.c_void_p,  # e
    ctypes.c_void_p,  # callback
    ctypes.c_void_p,  # callbackArg
    ctypes.c_void_p,  # decoderMemory
    ctypes.c_size_t,  # decoderMemorySize
]
OodleLZ_Decompress.restype = ctypes.c_size_t


def decompress_oodle(compressed_data):
    """Decompress Oodle-compressed data."""
    comp_buf = ctypes.create_string_buffer(compressed_data)
    raw_len = OodleLZ_GetDecodeBufferSize(comp_buf, len(compressed_data))
    if raw_len == 0:
        raise ValueError("Failed to get decode buffer size")
    print(f"  Expected decompressed size: {raw_len}")
    raw_buf = ctypes.create_string_buffer(raw_len)
    result = OodleLZ_Decompress(
        comp_buf, len(compressed_data),
        raw_buf, raw_len,
        0, 0, 0, None, None, None, None, None, 0
    )
    if result != raw_len:
        raise ValueError(f"Decompression failed: expected {raw_len}, got {result}")
    return bytes(raw_buf)


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

    print(f"UTOC: magic={magic.hex()}, version={version}, header_size={header_size}")
    print(f"Entries: {entry_count} (size={entry_size}), CB: {cb_count} (size={cb_entry_size})")

    # Parse entries (each entry is 24 bytes in v2)
    entries = []
    for i in range(entry_count):
        offset = header_size + i * entry_size
        entry_data = data[offset:offset+entry_size]
        if len(entry_data) >= 24:
            name_hash = entry_data[:20]
            off = struct.unpack('<Q', entry_data[20:28])[0]
            sz = struct.unpack('<I', entry_data[28:32])[0] if len(entry_data) >= 32 else 0
            flags = struct.unpack('<I', entry_data[32:36])[0] if len(entry_data) >= 36 else 0
            entries.append({'name_hash': name_hash, 'offset': off, 'size': sz, 'flags': flags})

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


def extract_iostore(utoc_path, ucas_path, output_dir):
    """Extract files from IoStore container."""
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"EXTRACTING: {os.path.basename(utoc_path)}")
    print(f"{'='*60}")

    utoc_info = parse_utoc(utoc_path)
    print(f"Container ID: {utoc_info['container_id'].hex()}")

    print(f"Reading UCAS: {ucas_path}")
    with open(ucas_path, 'rb') as f:
        ucas_data = f.read()
    print(f"UCAS size: {len(ucas_data)} bytes")

    # Extract each compressed block
    for i, cb in enumerate(utoc_info['cb_entries']):
        off = cb['offset']
        sz = cb['size']
        print(f"\nCB {i}: offset=0x{off:x} ({off}), size=0x{sz:x} ({sz})")
        if off >= len(ucas_data):
            print(f"  SKIP: offset beyond UCAS size")
            continue
        block_data = ucas_data[off:off+sz]
        if len(block_data) != sz:
            print(f"  WARNING: size mismatch (expected {sz}, got {len(block_data)})")
            if len(block_data) == 0:
                continue
        if len(block_data) == 0:
            print(f"  EMPTY block, skipping")
            continue
        # Check for Oodle magic
        if block_data[0] in (0xCC, 0xCD, 0xCE, 0xCF, 0xC0, 0xC1, 0xC2, 0xC3):
            print(f"  Oodle compressed (magic {block_data[0]:02x})")
            try:
                decompressed = decompress_oodle(block_data)
                out_path = os.path.join(output_dir, f'block_{i:03d}.bin')
                with open(out_path, 'wb') as f:
                    f.write(decompressed)
                print(f"    Decompressed: {len(decompressed)} bytes -> {out_path}")
                # Scan for uasset
                scan_for_uassets(decompressed, output_dir, f"block_{i:03d}_")
            except Exception as e:
                print(f"    Decompression FAILED: {e}")
                out_path = os.path.join(output_dir, f'block_{i:03d}_compressed.bin')
                with open(out_path, 'wb') as f:
                    f.write(block_data)
        else:
            print(f"  Not compressed (magic {block_data[0]:02x})")
            out_path = os.path.join(output_dir, f'block_{i:03d}.bin')
            with open(out_path, 'wb') as f:
                f.write(block_data)
            scan_for_uassets(block_data, output_dir, f"block_{i:03d}_")


def scan_for_uassets(data, output_dir, prefix=""):
    """Scan binary data for Unreal package headers and extract."""
    os.makedirs(output_dir, exist_ok=True)
    signatures = [
        (b'\x00\x00\x00\x00', 'package'),
        (b'BKHD', 'bnk'),
    ]
    for sig, name in signatures:
        pos = 0
        while True:
            pos = data.find(sig, pos)
            if pos < 0:
                break
            # Save reasonable chunk (up to 1MB)
            chunk_size = min(1000000, len(data) - pos)
            chunk = data[pos:pos+chunk_size]
            out_path = os.path.join(output_dir, f'{prefix}{name}_{pos}.bin')
            with open(out_path, 'wb') as f:
                f.write(chunk)
            print(f"    Found {name} at 0x{pos:x} -> {out_path} ({chunk_size} bytes)")
            pos += 4


def main():
    base = "/tmp/pc_extract/Paks"
    output_base = "/tmp/pakchunk0_extracted"

    # Extract 8-GV-RU_P
    extract_iostore(
        f"{base}/pakchunk0-WindowsNoEditor_8-GV-RU_P.utoc",
        f"{base}/pakchunk0-WindowsNoEditor_8-GV-RU_P.ucas",
        f"{output_base}/8-GV-RU_P"
    )

    # Extract 9-GV-RU_P (UTOC/UCAS, not the .pak)
    extract_iostore(
        f"{base}/pakchunk0-WindowsNoEditor_9-GV-RU_P.utoc",
        f"{base}/pakchunk0-WindowsNoEditor_9-GV-RU_P.ucas",
        f"{output_base}/9-GV-RU_P"
    )

if __name__ == '__main__':
    main()
