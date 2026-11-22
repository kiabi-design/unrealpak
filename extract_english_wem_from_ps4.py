
#!/usr/bin/env python3
"""
Extract 536 specific .wem files from PS4 pakchunk2-ps4.pak
Run this on your PC where you have the PS4 game files.
"""
import os
import json
import struct

# === CONFIGURE THESE PATHS ===
PAK_PATH = "pakchunk2-ps4.pak"           # Your PS4 pakchunk2 (815 MB)
FILELIST_PATH = "pak_filelist.txt"        # From earlier extraction
REPLACEMENTS_PATH = "pak_replacements.json"  # From this project
OUTPUT_DIR = "extracted_english_wem"      # Where to save extracted files
# ===============================

def parse_filelist(filelist_path):
    """Parse pak_filelist.txt to get filename -> offset, size"""
    mapping = {}
    with open(filelist_path, 'r') as f:
        for line in f:
            line = line.strip()
            if 'offset:' in line and 'size:' in line:
                # Format: LogPakFile: Display: "1000009927.wem" offset: 0, size: 6404, sha1: ...
                parts = line.split('"')
                if len(parts) >= 2:
                    filename = parts[1]
                    # Extract offset and size
                    import re
                    offset_match = re.search(r'offset:\s*(\d+)', line)
                    size_match = re.search(r'size:\s*(\d+)', line)
                    if offset_match and size_match:
                        offset = int(offset_match.group(1))
                        size = int(size_match.group(1))
                        mapping[filename] = (offset, size)
    return mapping

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Loading filelist...")
    filelist = parse_filelist(FILELIST_PATH)
    print(f"Loaded {len(filelist)} entries from filelist")

    print("Loading replacements...")
    with open(REPLACEMENTS_PATH, 'r') as f:
        replacements = json.load(f)
    print(f"Loaded {len(replacements)} replacements")

    print(f"Opening {PAK_PATH}...")
    with open(PAK_PATH, 'rb') as pak:
        extracted = 0
        for wwise_id, info in replacements.items():
            filename = f"{wwise_id}.wem"
            if filename in filelist:
                offset, size = filelist[filename]
                pak.seek(offset)
                data = pak.read(size)

                out_path = os.path.join(OUTPUT_DIR, filename)
                with open(out_path, 'wb') as f:
                    f.write(data)
                extracted += 1

                if extracted % 50 == 0:
                    print(f"  Extracted {extracted}/{len(replacements)}...")
            else:
                print(f"  WARNING: {filename} not in filelist")

        print(f"\nDone! Extracted {extracted} .wem files to {OUTPUT_DIR}/")
        print(f"Total size: {sum(os.path.getsize(os.path.join(OUTPUT_DIR, f)) for f in os.listdir(OUTPUT_DIR)) / 1024 / 1024:.1f} MB")

if __name__ == "__main__":
    main()
