#!/usr/bin/env python3
"""
Extract PS4 pakchunk2 using known file list, replace Russian audio, repack with UnrealPak.
"""

import json
import re
import os
import shutil
import subprocess
import struct

# Paths
PAK_FILE = "/home/user/Desktop/game-voice/PS4_extracted/PS4/pakchunk2-ps4.pak"
FILELIST = "/home/user/Desktop/game-voice/pak_filelist.txt"
REPLACEMENTS = "/home/user/Desktop/game-voice/pak_replacements.json"
EXTRACT_DIR = "/home/user/Desktop/game-voice/pak_extracted_full"
OUTPUT_PAK = "/home/user/Desktop/game-voice/pakchunk2-ps4_russian_unrealpak.pak"
UNREALPAK = "/home/user/Desktop/game-voice/UnrealPakTool/UnrealPakTool/UnrealPak.exe"

def parse_filelist():
    """Parse UnrealPak -List output to get file entries."""
    with open(FILELIST) as f:
        lines = f.readlines()

    entries = []
    for line in lines:
        # "filename.wem" offset: X, size: Y, sha1: Z, compression: None.
        m = re.search(r'"([^"]+)"\s+offset:\s+(\d+),\s+size:\s+(\d+)', line)
        if m:
            entries.append({
                'name': m.group(1),
                'offset': int(m.group(2)),
                'size': int(m.group(3))
            })
    return entries

def extract_files(entries, replacements_set):
    """Extract all files from pak to directory."""
    os.makedirs(EXTRACT_DIR, exist_ok=True)

    with open(PAK_FILE, 'rb') as pak:
        total = len(entries)
        for i, entry in enumerate(entries):
            # Determine output path
            rel_path = entry['name']
            out_path = os.path.join(EXTRACT_DIR, rel_path)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)

            # Read from pak
            pak.seek(entry['offset'])
            data = pak.read(entry['size'])

            # Write to disk
            with open(out_path, 'wb') as f:
                f.write(data)

            if (i + 1) % 5000 == 0:
                print(f"  Extracted {i+1}/{total} files...")

    print(f"Extraction complete: {total} files")

def replace_russian_audio(replacements):
    """Replace English .wem with Russian versions."""
    for wwise_id, info in replacements.items():
        russian_path = info['russian_file']
        # Find the extracted file path
        # The extracted file is at EXTRACT_DIR/WwiseAudio/PS4/English(US)/{wwise_id}.wem
        # But we need to find the actual path
        for root, dirs, files in os.walk(EXTRACT_DIR):
            for f in files:
                if f == f"{wwise_id}.wem":
                    out_path = os.path.join(root, f)
                    # Read Russian .wem and extract Opus data
                    with open(russian_path, 'rb') as rf:
                        rdata = rf.read()

                    # Find data chunk
                    data_idx = rdata.find(b'data')
                    if data_idx >= 0:
                        opus_size = struct.unpack('<I', rdata[data_idx+4:data_idx+8])[0]
                        opus_data = rdata[data_idx+8:data_idx+8+opus_size]

                        # Find nested RIFF
                        nested_pos = opus_data.find(b'RIFF')
                        if nested_pos > 0:
                            opus_data = opus_data[:nested_pos]

                        # Build PS4 RIFF container
                        fmt_data = bytes.fromhex(
                            "ffff0100c05d0000e20a000000000000300000000141000021df0100b2000000a23700000000"
                            "5f01d4010000860200006e005f011c450000c446000088f5ce20090a"
                        )
                        fmt_size = len(fmt_data)
                        data_size = len(opus_data)
                        riff_size = (8 + fmt_size) + (8 + data_size)

                        new_riff = bytearray()
                        new_riff.extend(b'RIFF')
                        new_riff.extend(struct.pack('<I', riff_size))
                        new_riff.extend(b'WAVE')
                        new_riff.extend(b'fmt ')
                        new_riff.extend(struct.pack('<I', fmt_size))
                        new_riff.extend(fmt_data)
                        new_riff.extend(b'data')
                        new_riff.extend(struct.pack('<I', data_size))
                        new_riff.extend(opus_data)

                        with open(out_path, 'wb') as f:
                            f.write(new_riff)
                    break

    print(f"Replaced {len(replacements)} audio files")

def create_response_file(entries):
    """Create UnrealPak response file."""
    response_path = "/home/user/Desktop/game-voice/pak_response.txt"
    with open(response_path, 'w') as f:
        for entry in entries:
            rel_path = entry['name']
            abs_path = os.path.join(EXTRACT_DIR, rel_path).replace('\\', '/')
            # Response file format: "path" "abspath"
            f.write(f'"{rel_path}" "{abs_path}"\n')
    print(f"Response file created: {response_path}")
    return response_path

def main():
    print("=" * 60)
    print("FULL REPACK WITH UNREALPAK")
    print("=" * 60)

    # Load replacements
    with open(REPLACEMENTS) as f:
        replacements = json.load(f)

    print(f"Loaded {len(replacements)} replacements")

    # Parse file list
    print("Parsing file list...")
    entries = parse_filelist()
    print(f"Total files in pak: {len(entries)}")

    # Extract all files
    print("Extracting files from pak...")
    replacements_set = set(replacements.keys())
    extract_files(entries, replacements_set)

    # Replace Russian audio
    print("Replacing Russian audio...")
    replace_russian_audio(replacements)

    # Create response file
    print("Creating response file...")
    response_file = create_response_file(entries)

    # Repack with UnrealPak
    print("Repacking with UnrealPak...")
    cmd = [
        'wine', UNREALPAK,
        OUTPUT_PAK,
        f'-Create={response_file}',
        '-compress'
    ]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    print(f"Return code: {result.returncode}")
    if result.stdout:
        print(f"STDOUT: {result.stdout[-2000:]}")
    if result.stderr:
        print(f"STDERR: {result.stderr[-2000:]}")

if __name__ == '__main__':
    main()