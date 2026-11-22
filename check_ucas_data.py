with open('/home/user/Desktop/game-voice/extracted_PC/Paks/pakchunk0-WindowsNoEditor_9-GV-RU_P.ucas', 'rb') as f:
    data = f.read()

# Check data after first few paths
paths_to_check = [
    0x42,  # /Game/Audio/...
    0x19e, # /Game/Narrative/LocalisedStrings/UI_Strings
    0x203, # /Game/UI/Fonts/R8/R8_Menu_Captions
]

for offset in paths_to_check:
    # Find null terminator
    null_pos = data.find(b'\x00', offset)
    if null_pos >= 0:
        asset_start = null_pos + 1
        print(f"\nPath at 0x{offset:x}:")
        print(f"  Null at 0x{null_pos:x}, asset starts at 0x{asset_start:x}")
        # Print first 64 bytes of asset data
        asset_preview = data[asset_start:asset_start+64]
        print(f"  First 64 bytes: {asset_preview.hex()}")
        print(f"  As text: {asset_preview.decode('utf-8', errors='ignore')}")

