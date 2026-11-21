#!/usr/bin/env python3
"""Reassemble split files in GitHub Actions"""
import os
import glob

def reassemble(base_name, output_dir="."):
    parts = sorted(glob.glob(f"{base_name}.part*"))
    if not parts:
        return
    output_path = os.path.join(output_dir, base_name)
    print(f"Reassembling {base_name} from {len(parts)} parts...")
    with open(output_path, 'wb') as out:
        for part in parts:
            with open(part, 'rb') as f:
                out.write(f.read())
    print(f"  Done: {output_path} ({os.path.getsize(output_path)} bytes)")

if __name__ == "__main__":
    reassemble("pakchunk2-WindowsNoEditor_9-GV-RU_P.pak", "extracted_PC/Paks/")
    reassemble("pakchunk2_decrypted.pak", "extracted_PC/Paks/")
