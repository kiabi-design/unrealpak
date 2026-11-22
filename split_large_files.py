#!/usr/bin/env python3
"""
Split large files into 100MB chunks for GitHub (100MB limit per file)
"""
import os

CHUNK_SIZE = 100 * 1024 * 1024  # 100 MB

def split_file(filepath):
    filename = os.path.basename(filepath)
    dirpath = os.path.dirname(filepath)
    size = os.path.getsize(filepath)
    
    if size <= CHUNK_SIZE:
        print(f"{filename}: {size} bytes - no split needed")
        return
    
    num_chunks = (size + CHUNK_SIZE - 1) // CHUNK_SIZE
    print(f"{filename}: {size} bytes -> {num_chunks} chunks")
    
    with open(filepath, 'rb') as f:
        for i in range(num_chunks):
            chunk = f.read(CHUNK_SIZE)
            chunk_path = f"{filepath}.part{i:03d}"
            with open(chunk_path, 'wb') as out:
                out.write(chunk)
            print(f"  Created {os.path.basename(chunk_path)} ({len(chunk)} bytes)")

def create_reassemble_script():
    script = '''#!/usr/bin/env python3
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
'''
    with open("/home/user/Desktop/game-voice/reassemble_parts.py", "w") as f:
        f.write(script)
    print("Created reassemble_parts.py")

if __name__ == "__main__":
    # Split the large pakchunk2 files
    split_file("/home/user/Desktop/game-voice/extracted_PC/Paks/pakchunk2-WindowsNoEditor_9-GV-RU_P.pak")
    split_file("/home/user/Desktop/game-voice/extracted_PC/Paks/pakchunk2_decrypted.pak")
    create_reassemble_script()
