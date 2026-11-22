#!/usr/bin/env python3
"""
Scan .bnk files for hidden .wem streams inside DATA sections.
GameVoice PC mod may have additional audio embedded in soundbanks.
"""

import os
import struct
import json

def find_wem_in_bnk(bnk_path):
    """Find all RIFF/WAVE chunks inside a .bnk file."""
    with open(bnk_path, 'rb') as f:
        data = f.read()

    results = []

    # Search for RIFF markers
    pos = 0
    while True:
        riff_pos = data.find(b'RIFF', pos)
        if riff_pos < 0:
            break

        # Check if it's a WAVE
        if riff_pos + 12 <= len(data):
            riff_size = struct.unpack('<I', data[riff_pos+4:riff_pos+8])[0]
            if data[riff_pos+8:riff_pos+12] == b'WAVE':
                # Found a WAVE chunk
                wave_end = riff_pos + 8 + riff_size

                # Search for data chunk inside
                search_start = riff_pos + 12
                search_end = min(wave_end, len(data))
                data_chunk_pos = data.find(b'data', search_start, search_end)

                audio_data = None
                audio_size = 0
                if data_chunk_pos >= 0 and data_chunk_pos + 8 <= len(data):
                    audio_size = struct.unpack('<I', data[data_chunk_pos+4:data_chunk_pos+8])[0]
                    audio_data_start = data_chunk_pos + 8
                    audio_data_end = audio_data_start + audio_size
                    if audio_data_end <= len(data):
                        audio_data = data[audio_data_start:audio_data_end]

                results.append({
                    'bnk_offset': riff_pos,
                    'riff_size': riff_size,
                    'total_size': riff_size + 8,
                    'data_chunk_offset': data_chunk_pos - riff_pos if data_chunk_pos >= 0 else None,
                    'audio_size': audio_size,
                    'has_audio': audio_data is not None,
                    'audio_data': audio_data.hex()[:100] if audio_data else None
                })

        pos = riff_pos + 4

    return results

def scan_all_bnks(bnk_dir):
    """Scan all .bnk files in directory."""
    all_results = {}

    for fname in sorted(os.listdir(bnk_dir)):
        if fname.endswith('.bnk'):
            bnk_path = os.path.join(bnk_dir, fname)
            print(f"Scanning {fname}...")
            wems = find_wem_in_bnk(bnk_path)
            if wems:
                all_results[fname] = wems
                print(f"  Found {len(wems)} RIFF/WAVE chunks")
                for w in wems:
                    if w['has_audio']:
                        print(f"    Offset 0x{w['bnk_offset']:X}: RIFF size {w['riff_size']}, audio {w['audio_size']} bytes")

    return all_results

def extract_audio_from_bnk(bnk_path, output_dir):
    """Extract all audio chunks from a .bnk file."""
    os.makedirs(output_dir, exist_ok=True)

    with open(bnk_path, 'rb') as f:
        data = f.read()

    extracted = []
    pos = 0
    count = 0
    while True:
        riff_pos = data.find(b'RIFF', pos)
        if riff_pos < 0:
            break

        if riff_pos + 12 <= len(data):
            riff_size = struct.unpack('<I', data[riff_pos+4:riff_pos+8])[0]
            if data[riff_pos+8:riff_pos+12] == b'WAVE':
                wave_end = riff_pos + 8 + riff_size
                search_start = riff_pos + 12
                search_end = min(wave_end, len(data))
                data_chunk_pos = data.find(b'data', search_start, search_end)

                if data_chunk_pos >= 0 and data_chunk_pos + 8 <= len(data):
                    audio_size = struct.unpack('<I', data[data_chunk_pos+4:data_chunk_pos+8])[0]
                    audio_data_start = data_chunk_pos + 8
                    audio_data_end = audio_data_start + audio_size
                    if audio_data_end <= len(data):
                        audio_data = data[audio_data_start:audio_data_end]

                        # Save as .wem
                        out_name = f"{os.path.basename(bnk_path)}_wem_{count:03d}.wem"
                        out_path = os.path.join(output_dir, out_name)
                        with open(out_path, 'wb') as out:
                            out.write(audio_data)

                        extracted.append({
                            'file': out_name,
                            'bnk_offset': riff_pos,
                            'audio_size': audio_size
                        })
                        count += 1

        pos = riff_pos + 4

    return extracted

def main():
    # Scan PC mod .bnk files
    pc_bnk_dir = "/home/user/Desktop/game-voice/extracted_audio_pc"
    output_dir = "/home/user/Desktop/game-voice/bnk_hidden_audio"

    print("=" * 60)
    print("SCANNING PC GAMEVOICE .BNK FILES FOR HIDDEN AUDIO")
    print("=" * 60)

    all_results = scan_all_bnks(pc_bnk_dir)

    total_chunks = sum(len(v) for v in all_results.values())
    total_with_audio = sum(1 for v in all_results.values() for w in v if w['has_audio'])

    print(f"\n{'=' * 60}")
    print(f"SUMMARY:")
    print(f"  .bnk files scanned: {len(all_results)}")
    print(f"  Total RIFF/WAVE chunks: {total_chunks}")
    print(f"  Chunks with audio data: {total_with_audio}")
    print(f"{'=' * 60}")

    # Save results
    with open("/home/user/Desktop/game-voice/bnk_scan_results.json", 'w') as f:
        json.dump(all_results, f, indent=2)

    print("\nExtracting audio from all chunks...")
    total_extracted = 0
    for fname, wems in all_results.items():
        bnk_path = os.path.join(pc_bnk_dir, fname)
        extracted = extract_audio_from_bnk(bnk_path, output_dir)
        total_extracted += len(extracted)
        if extracted:
            print(f"  {fname}: extracted {len(extracted)} audio chunks")

    print(f"\nTotal extracted audio chunks: {total_extracted}")
    print(f"Saved to: {output_dir}")

if __name__ == '__main__':
    main()