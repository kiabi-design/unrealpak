#!/usr/bin/env python3
"""
Opus replacement with truncation to fit PS4 slots.
Extracts Opus from Russian .wem, truncates to fit PS4 slot, repackages in PS4 RIFF.
"""

import struct
import os
import json
import shutil

# Paths
PS4_PAK = "/home/user/Desktop/game-voice/PS4_extracted/PS4/pakchunk2-ps4.pak"
OUTPUT_PAK = "/home/user/Desktop/game-voice/pakchunk2-ps4_russian_complete.pak"
RUSSIAN_WEM_DIR = "/home/user/Desktop/game-voice/pc_russian_audio_v2"
REPLACEMENT_PLAN = "/home/user/Desktop/game-voice/ps4_pakchunk2_full_replacement_plan.json"

# PS4 Opus fmt template (24kHz)
PS4_FMT_DATA = bytes.fromhex(
    "ffff0100c05d0000e20a000000000000300000000141000021df0100b2000000a23700000000"
    "5f01d4010000860200006e005f011c450000c446000088f5ce20090a"
)

# PS4 Opus fmt template (32kHz)
PS4_FMT_DATA_32K = bytes.fromhex(
    "ffff0100c07d0000e409000000000000300000000141000021df0100b2000000de2b00000000"
    "5f01d4010000860200006e005f011c450000c446000088f5ce20090a"
)

def extract_opus_from_russian_wem(wem_path):
    """Extract Opus payload from Russian .wem file."""
    with open(wem_path, 'rb') as f:
        data = f.read()

    data_idx = data.find(b'data')
    if data_idx < 0:
        return None

    data_size = struct.unpack('<I', data[data_idx+4:data_idx+8])[0]
    opus_data = data[data_idx+8:data_idx+8+data_size]
    return opus_data

def build_ps4_riff(opus_data, sample_rate=24000):
    """Build a proper PS4 RIFF container with Opus data (no fact chunk to save space)."""
    data_size = len(opus_data)

    # Choose fmt template based on sample rate
    if sample_rate == 32000:
        fmt_data = PS4_FMT_DATA_32K
    else:
        fmt_data = PS4_FMT_DATA
        if sample_rate != 24000:
            fmt_data = bytearray(fmt_data)
            struct.pack_into('<I', fmt_data, 4, sample_rate)
            byte_rate = int(sample_rate * 1.2)
            struct.pack_into('<I', fmt_data, 8, byte_rate)
            fmt_data = bytes(fmt_data)

    fmt_size = len(fmt_data)

    # RIFF structure WITHOUT fact chunk (saves 12 bytes):
    # RIFF header (12): "RIFF" + size + "WAVE"
    # fmt chunk (8 + fmt_size): "fmt " + size + fmt_data
    # data chunk (8 + data_size): "data" + size + opus_data

    riff_size = (8 + fmt_size) + (8 + data_size)

    riff = bytearray()
    riff.extend(b'RIFF')
    riff.extend(struct.pack('<I', riff_size))
    riff.extend(b'WAVE')

    # fmt chunk
    riff.extend(b'fmt ')
    riff.extend(struct.pack('<I', fmt_size))
    riff.extend(fmt_data)

    # data chunk
    riff.extend(b'data')
    riff.extend(struct.pack('<I', data_size))
    riff.extend(opus_data)

    return bytes(riff)

def get_ps4_sample_rate_at_offset(pak_file, offset):
    """Read sample rate from PS4 RIFF at given offset."""
    pak_file.seek(offset + 12)
    fmt_header = pak_file.read(8)
    if fmt_header[:4] != b'fmt ':
        data = pak_file.read(200)
        idx = data.find(b'fmt ')
        if idx >= 0:
            pak_file.seek(offset + 12 + idx)
            fmt_header = pak_file.read(8)
        else:
            return 24000
    fmt_size = struct.unpack('<I', fmt_header[4:8])[0]
    fmt_data = pak_file.read(fmt_size)
    if fmt_size >= 8:
        sample_rate = struct.unpack('<I', fmt_data[4:8])[0]
        return sample_rate
    return 24000

def main():
    print("=" * 60)
    print("OPUS REPLACEMENT WITH TRUNCATION - ALL MATCHED FILES")
    print("=" * 60)

    with open(REPLACEMENT_PLAN) as f:
        plan = json.load(f)

    print(f"Loaded {len(plan)} replacement entries")

    # Copy original pak
    print(f"Copying {PS4_PAK} -> {OUTPUT_PAK}")
    shutil.copy2(PS4_PAK, OUTPUT_PAK)

    # Get list of Russian .wem files
    russian_files = {}
    for fname in os.listdir(RUSSIAN_WEM_DIR):
        if fname.endswith('.wem'):
            parts = fname.replace('.wem', '').split('_')
            manifest_id = int(parts[-1])
            russian_files[manifest_id] = fname

    print(f"Found {len(russian_files)} Russian .wem files")

    # Process each replacement entry
    with open(OUTPUT_PAK, 'r+b') as f:
        success = 0
        failed = 0
        missing = 0
        truncated = 0

        for i, entry in enumerate(plan):
            manifest_id = entry['manifest_id']
            ps4_offset = entry['ps4_pak_offset']
            ps4_total_size = entry['ps4_total_size']

            # Find Russian file
            if manifest_id not in russian_files:
                missing += 1
                continue

            russian_fname = russian_files[manifest_id]
            russian_path = os.path.join(RUSSIAN_WEM_DIR, russian_fname)

            # Extract Opus payload
            opus_data = extract_opus_from_russian_wem(russian_path)
            if opus_data is None:
                failed += 1
                continue

            # Get PS4 sample rate at this offset
            sample_rate = get_ps4_sample_rate_at_offset(f, ps4_offset)

            # Calculate available Opus slot size
            # RIFF overhead without fact chunk: 12 (RIFF) + 8+66 (fmt) + 8 (data header) = 94
            opus_slot = ps4_total_size - 94

            # Truncate if needed
            if len(opus_data) > opus_slot:
                opus_data = opus_data[:opus_slot]
                truncated += 1

            # Build new RIFF
            new_riff = build_ps4_riff(opus_data, sample_rate)
            new_size = len(new_riff)

            # Verify it fits
            if new_size > ps4_total_size + 8:
                print(f"  [{i}] manifest_id {manifest_id}: STILL TOO LARGE ({new_size} > {ps4_total_size + 8})")
                failed += 1
                continue

            # Write new RIFF (pad with zeros if smaller)
            f.seek(ps4_offset)
            f.write(new_riff)
            if new_size < ps4_total_size + 8:
                f.write(b'\x00' * (ps4_total_size + 8 - new_size))

            success += 1
            if success % 50 == 0:
                print(f"  Progress: {success} replaced...")

    print(f"\n{'=' * 60}")
    print(f"RESULTS:")
    print(f"  Success: {success}")
    print(f"  Failed: {failed}")
    print(f"  Missing Russian files: {missing}")
    print(f"  Truncated: {truncated}")
    print(f"  Total plan entries: {len(plan)}")
    print(f"  Russian files available: {len(russian_files)}")
    print(f"{'=' * 60}")

    # Verify RIFF headers
    print("\nVerifying RIFF headers...")
    verify_count = 0
    with open(OUTPUT_PAK, 'rb') as f:
        for entry in plan[:100]:
            f.seek(entry['ps4_pak_offset'])
            riff = f.read(12)
            if riff[:4] == b'RIFF' and riff[8:12] == b'WAVE':
                verify_count += 1
    print(f"  Valid RIFF headers in first 100: {verify_count}/100")

if __name__ == '__main__':
    main()