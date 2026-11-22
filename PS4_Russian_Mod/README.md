# PS4 Russian Voice Mod - GameVoice

## Files Created

### pakchunk2 (Audio - 364 Russian .wem files replaced)
- `pakchunk2-ps4_russian.pak` - 612.8 MB - UE4 pak v11 with Russian audio
- `pakchunk2-ps4_russian.utoc` - 245 B - IoStore table of contents
- `pakchunk2-ps4_russian.ucas` - 48 B - IoStore container

### pakchunk0 (Localization/Text - Placeholder, needs completion)
- `pakchunk0-ps4.pak` - 6 KB - UE4 pak v11 with 38 asset entries (placeholder data)
- `pakchunk0-ps4.utoc` - 358 B - IoStore table of contents
- `pakchunk0-ps4.ucas` - 48 B - IoStore container

## What's Done

### pakchunk2 (Audio) - COMPLETE ✓
- Extracted 536 Russian .wem files from PC GameVoice mod
- Mapped 364 Russian files to PS4 pakchunk2 via Wwise ID matching
- Created new PS4 pakchunk2 with 364 Russian audio replacements
- Used custom Python UE4 pak v11 creator (create_pak_v2.py) since UnrealPak crashes under Wine
- Verified pak structure matches original PS4 format

### pakchunk0 (Localization/Text) - NEEDS COMPLETION
- Extracted asset registry from PC GameVoice mod (9-GV-RU_P UCAS)
- Found 38 asset paths including:
  - Narrative/LocalisedStrings/UI_Strings
  - UI/Fonts/R8/R8_Menu_Captions
  - Audio/Enums/SpeakerOutput
  - UI/GameMenu/LoadableScreenWidgets/Settings_Audio_V2
  - Script/SwGame (core game scripts)
- Created placeholder pakchunk0 with these 38 entries
- **MISSING**: Actual .uasset file data (compressed in PC mod's 8-GV-RU_P UCAS and 9-GV-RU_P .pak)

## What's Needed to Complete pakchunk0

### Option 1: Decompress PC Mod Containers (Recommended)
The PC GameVoice mod stores actual asset data in Oodle-compressed containers:
- `pakchunk0-WindowsNoEditor_8-GV-RU_P.ucas` (114 KB) - 12 Oodle-compressed blocks
- `pakchunk0-WindowsNoEditor_9-GV-RU_P.pak` (2.4 MB) - Compressed asset data

To decompress, you need the Oodle library:
1. Download `liboo2core_9.so` (Linux) or `oo2core_9_win64.dll` (Windows)
2. Run: `python3 decompress_iostore.py <utoc> <ucas> <output_dir>`
3. Extract .uasset files from decompressed blocks
4. Rebuild pakchunk0-ps4.pak with actual asset data

### Option 2: Use Original PS4 pakchunk0
If you have the original PS4 pakchunk0 files:
1. Extract original PS4 pakchunk0 (UE4 pak v11)
2. Replace English localization assets with Russian ones from PC mod
3. Repack as PS4 pakchunk0

## Scripts Available

- `create_pak_v2.py` - Creates UE4 pak v11 from response file (used for pakchunk2)
- `create_pakchunk0_ps4.py` - Creates PS4 pakchunk0 from PC asset registry
- `decompress_iostore.py` - Decompresses IoStore containers using Oodle
- `extract_iostore.py` - Parses IoStore UTOC/UCAS structure
- `replace_opus_final.py` - Replaces audio in PS4 pak (for pakchunk2)
- `scan_bnk_for_wem.py` - Scans .bnk for embedded .wem files

## Installation on PS4

Copy these 6 files to your PS4 game directory:
```
/pakchunk0-ps4.pak
/pakchunk0-ps4.utoc
/pakchunk0-ps4.ucas
/pakchunk2-ps4_russian.pak
/pakchunk2-ps4_russian.utoc
/pakchunk2-ps4_russian.ucas
```

Replace the original `pakchunk2-ps4.pak/.utoc/.ucas` with the `_russian` versions.
For pakchunk0, replace or add the new files (original PS4 may not have pakchunk0).

## Notes

- **SwGame**: The PC mod references `/Script/SwGame` extensively. This is the core game module. Ensure PS4 version has compatible SwGame assets.
- **Container ID**: Both pakchunk0 and pakchunk2 use container ID `c12719ab10631d4b` (from PS4 pakchunk2)
- **Audio Format**: PS4 uses Opus codec (24kHz mono for voices). PC .wem files were converted by keeping PS4 RIFF/fmt headers and replacing PCM data.
- **536 Russian Files**: Total in PC mod. 364 matched and replaced in pakchunk2. Remaining 172 may be in pakchunk0 or unmatched.

## Next Steps

1. Obtain Oodle library (`liboo2core_9.so`) to decompress PC mod's pakchunk0
2. Extract actual .uasset files from decompressed blocks
3. Rebuild pakchunk0-ps4.pak with real Russian localization data
4. Test on PS4

## Contact

For issues or questions, refer to the GameVoice mod page: https://www.gamesvoice.ru/product/swsurvivor