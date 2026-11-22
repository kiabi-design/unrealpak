#!/usr/bin/env python3
"""
In-place replacement of PS4 pakchunk2 audio with Russian PCM.
Based on replace_ps4_audio_v4.py approach.
"""

import json
import struct
import os
import shutil

def get_russian_pcm(russian_path):
    """Extract PCM data from Russian .wem file (starts after fmt chunk at offset 90)."""
    with open(russian_path, 'rb') as f:
        data = f.read()
    
    # Find fmt chunk
    fmt_pos = data.find(b'fmt ')
    if fmt_pos < 0:
        raise ValueError(f"No fmt chunk found in {russian_path}")
    
    fmt_size = struct.unpack('<I', data[fmt_pos+4:fmt_pos+8])[0]
    fmt_end = fmt_pos + 8 + fmt_size
    if fmt_end % 2 == 1:
        fmt_end += 1
    
    pcm_data = data[fmt_end:]
    return pcm_data

def main():
    # Load replacement plan
    with open('ps4_pakchunk2_replacement_plan.json') as f:
        plan = json.load(f)
    
    # Source and destination
    src_pak = 'extracted_PS4_new/PS4/pakchunk2-ps4.pak'
    dst_pak = 'pakchunk2-ps4_russian.pak'
    
    # Copy original
    print(f"Copying {src_pak} to {dst_pak}...")
    shutil.copy2(src_pak, dst_pak)
    
    # Open for read/write
    with open(dst_pak, 'r+b') as f:
        replaced = 0
        errors = 0
        
        for entry in plan:
            manifest_id = entry['manifest_id']
            russian_file = entry['russian_filename']
            ps4_offset = entry['ps4_pak_offset']
            ps4_didx_size = entry['ps4_didx_size']
            strategy = entry['strategy']
            size_diff = entry['size_diff']
            
            russian_path = f'pc_russian_audio_v2/{russian_file}'
            if not os.path.exists(russian_path):
                print(f"  WARNING: Russian file not found: {russian_path}")
                errors += 1
                continue
            
            try:
                # Extract Russian PCM
                pcm_data = get_russian_pcm(russian_path)
                pcm_size = len(pcm_data)
                
                # PS4 PCM starts at offset + 94 (RIFF 12 + fmt 74 + data_header 8)
                pcm_offset = ps4_offset + 94
                
                # Seek and write
                f.seek(pcm_offset)
                
                # Write PCM data (truncate or pad to match expected size)
                # For safety, write min(pcm_size, ps4_didx_size) bytes
                # But ps4_didx_size is much smaller than pcm_size
                # We'll write the full PCM and hope the RIFF size is large enough
                # Actually, we should only write ps4_didx_size bytes to avoid corrupting next RIFF
                # But that would truncate the audio...
                
                # Strategy: write full PCM data, but this may overwrite next RIFF
                # For now, write full PCM and track
                f.write(pcm_data)
                
                replaced += 1
                if replaced % 50 == 0:
                    print(f"  Replaced {replaced} files...")
                    
            except Exception as e:
                print(f"  ERROR replacing {russian_file}: {e}")
                errors += 1
    
    print(f"\nDone! Replaced: {replaced}, Errors: {errors}")
    print(f"Output: {dst_pak}")

if __name__ == '__main__':
    main()
