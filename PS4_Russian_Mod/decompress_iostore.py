#!/usr/bin/env python3
"""
Decompress UE5 IoStore containers using Oodle.
Requires liboo2core_9.so (Linux) or oo2core_9_win64.dll (Windows via Wine).
"""

import os
import struct
import ctypes
import sys

# Try to load Oodle library
OODLE_LIB = None
for lib_name in ['liboo2core_9.so', 'oo2core_9_win64.dll', './liboo2core_9.so', './oo2core_9_win64.dll']:
    try:
        if lib_name.endswith('.dll'):
            # Would need Wine - skip for now
            continue
        OODLE_LIB = ctypes.CDLL(lib_name)
        print(f"Loaded Oodle library: {lib_name}")
        break
    except Exception as e:
        print(f"Failed to load {lib_name}: {e}")

if OODLE_LIB is None:
    print("ERROR: Could not load Oodle library.")
    print("Please download liboo2core_9.so (Linux) or oo2core_9_win64.dll (Windows)")
    print("and place it in the current directory.")
    sys.exit(1)

# Oodle function signatures
# OodleLZ_Decompress(compBuf, compBufSize, rawBuf, rawLen, fuzzSafe, crc, verbose, dstBase, e, callback, callbackArg, decoderMemory, decoderMemorySize)
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

# OodleLZ_GetDecodeBufferSize
OodleLZ_GetDecodeBufferSize = OODLE_LIB.OodleLZ_GetDecodeBufferSize
OodleLZ_GetDecodeBufferSize.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
OodleLZ_GetDecodeBufferSize.restype = ctypes.c_size_t


def decompress_oodle(compressed_data):
    """Decompress Oodle-compressed data."""
    # Get required buffer size
    raw_len = OodleLZ_GetDecodeBufferSize(compressed_data, len(compressed_data))
    if raw_len == 0:
        raise ValueError("Failed to get decode buffer size")

    # Allocate output buffer
    raw_buf = ctypes.create_string_buffer(raw_len)

    # Decompress
    result = OodleLZ_Decompress(
        compressed_data, len(compressed_data),
        raw_buf, raw_len,
        0,  # fuzzSafe
        0,  # crc
        0,  # verbose
        None, None, None, None,  # dstBase, e, callback, callbackArg
        None, 0  # decoderMemory, decoderMemorySize
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

    # Parse entries
    entries = []
    for i in range(entry_count):
        offset = header_size + i * entry_size
        entry_data = data[offset:offset+entry_size]
        if len(entry_data) >= 12:
            off = struct.unpack('<Q', entry_data[:8])[0]
            sz = struct.unpack('<I', entry_data[8:12])[0]
            entries.append({'offset': off, 'size': sz})

    # Parse compressed block entries (8 bytes each, at header_size + entry_count*entry_size)
    cb_start = header_size + entry_count * entry_size
    cb_entries = []
    for i in range(cb_count):
        offset = cb_start + i * 8
        if offset + 8 <= len(data):
            cb_data = data[offset:offset+8]
            # Try to parse as offset(4) + size(4)
            cb_off = struct.unpack('<I', cb_data[:4])[0]
            cb_sz = struct.unpack('<I', cb_data[4:8])[0]
            cb_entries.append({'offset': cb_off, 'size': cb_sz})

    return {
        'version': version,
        'header_size': header_size,
        'entries': entries,
        'cb_entries': cb_entries,
        'container_id': data[0x30:0x38]
    }


def extract_iostore(utoc_path, ucas_path, output_dir):
    """Extract files from IoStore container."""
    os.makedirs(output_dir, exist_ok=True)

    print(f"Parsing UTOC: {utoc_path}")
    utoc_info = parse_utoc(utoc_path)
    print(f"  Version: {utoc_info['version']}")
    print(f"  Entries: {len(utoc_info['entries'])}")
    print(f"  CB Entries: {len(utoc_info['cb_entries'])}")
    print(f"  Container ID: {utoc_info['container_id'].hex()}")

    print(f"Reading UCAS: {ucas_path}")
    with open(ucas_path, 'rb') as f:
        ucas_data = f.read()

    print(f"UCAS size: {len(ucas_data)} bytes")

    # Extract each compressed block
    for i, cb in enumerate(utoc_info['cb_entries']):
        off = cb['offset']
        sz = cb['size']

        if off >= len(ucas_data):
            print(f"  CB {i}: offset {off} beyond UCAS size, skipping")
            continue

        block_data = ucas_data[off:off+sz]
        if len(block_data) != sz:
            print(f"  CB {i}: size mismatch (expected {sz}, got {len(block_data)})")
            continue

        # Check for Oodle magic
        if len(block_data) > 0 and block_data[0] in (0xCC, 0xCD, 0xCE, 0xCF, 0xC0):
            print(f"  CB {i}: Oodle compressed (magic {block_data[0]:02x}), offset={off}, size={sz}")
            try:
                decompressed = decompress_oodle(block_data)
                out_path = os.path.join(output_dir, f'block_{i:03d}.bin')
                with open(out_path, 'wb') as f:
                    f.write(decompressed)
                print(f"    Decompressed: {len(decompressed)} bytes -> {out_path}")
            except Exception as e:
                print(f"    Decompression failed: {e}")
                # Save compressed anyway
                out_path = os.path.join(output_dir, f'block_{i:03d}_compressed.bin')
                with open(out_path, 'wb') as f:
                    f.write(block_data)
        else:
            print(f"  CB {i}: Not compressed (magic {block_data[0]:02x if block_data else 'empty'}), offset={off}, size={sz}")
            out_path = os.path.join(output_dir, f'block_{i:03d}.bin')
            with open(out_path, 'wb') as f:
                f.write(block_data)


def main():
    if len(sys.argv) < 4:
        print("Usage: python3 decompress_iostore.py <utoc> <ucas> <output_dir>")
        sys.exit(1)

    utoc_path = sys.argv[1]
    ucas_path = sys.argv[2]
    output_dir = sys.argv[3]

    extract_iostore(utoc_path, ucas_path, output_dir)


if __name__ == '__main__':
    main()