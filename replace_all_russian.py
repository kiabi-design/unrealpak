#!/usr/bin/env python3
"""
In-place replacement of ALL matched Russian audio in PS4 pakchunk2.
"""

import json
import struct
import os
import shutil

def get_russian_pcm(russian_path):
    """Extract PCM data from Russian .wem file."""
    with open(russian_path, 'rb') as f:
        data = f.read()
    
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
    with open('ps4_pakchunk2_full_replacement_plan.json') as f:
        plan = json.load(f)
    
    src_pak = 'extracted_PS4_new/PS4/pakchunk2-ps4.pak'
    dst_pak = 'pakchunk2-ps4_russian_full.pak'
    
    print(f"Copying {src_pak} to {dst_pak}...")
    shutil.copy2(src_pak, dst_pak)
    
    with open(dst_pak, 'r+b') as f:
        replaced = 0
        errors = 0
        
        for entry in plan:
            russian_file = entry['russian_filename']
            ps4_offset = entry['ps4_pak_offset']
            ps4_total_size = entry['ps4_total_size']
            ps4_didx_size = entry['ps4_didx_size']
            
            russian_path = f'pc_russian_audio_v2/{russian_file}'
            if not os.path.exists(russian_path):
                print(f"  WARNING: Russian file not found: {russian_path}")
                errors += 1
                continue
            
            try:
                pcm_data = get_russian_pcm(russian_path)
                
                # PS4 PCM starts at offset + 94 (RIFF 12 + fmt 74 + data_header 8)
                pcm_offset = ps4_offset + 94
                
                # Available space in RIFF data chunk
                available = ps4_total_size - 94
                
                # Truncate or pad to fit
                if len(pcm_data) > available:
                    pcm_data = pcm_data[:available]
                    print(f"  Truncated {russian_file}: {len(pcm_data)} -> {available}")
                elif len(pcm_data) < available:
                    pcm_data = pcm_data + b'\x00' * (available - len(pcm_data))
                
                f.seek(pcm_offset)
                f.write(pcm_data)
                
                replaced += 1
                if replaced % 50 == 0:
                    print(f"  Replaced {replaced}/{len(plan)} files...")
                    
            except Exception as e:
                print(f"  ERROR replacing {russian_file}: {e}")
                errors += 1
    
    print(f"\nDone! Replaced: {replaced}, Errors: {errors}")
    print(f"Output: {dst_pak}")

if __name__ == '__main__':
    main()
