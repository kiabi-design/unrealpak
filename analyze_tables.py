import struct, json

pak_path = "/home/user/Desktop/game-voice/pakchunk1-ps4.pak"
with open(pak_path, "rb") as f:
    pak_data = f.read()

with open("ps4_replacement_plan.json", "r") as f:
    plan = json.load(f)

known = {p['manifest_id']: p['pak_offset'] for p in plan if p['confidence'] == 'unique_size' and p['pak_offset']}

bnk_positions = [
    (0x30F60035, "bnk_0"),
    (0x32170035, "bnk_1"),
    (0x328E0035, "bnk_2"),
    (0x329E0035, "bnk_3"),
    (0x33040035, "bnk_4"),
    (0x33370035, "bnk_5"),
    (0x34893AF8, "bnk_6"),
    (0x34920035, "bnk_7"),
    (0x35210035, "bnk_8"),
    (0x35400035, "bnk_9"),
    (0x35570035, "bnk_10"),
    (0x35C10035, "bnk_11"),
    (0x35D00035, "bnk_12"),
    (0x35DF0035, "bnk_13"),
    (0x35F60035, "bnk_14"),
    (0x360B5B33, "bnk_15"),
    (0x36130035, "bnk_16"),
    (0x36270035, "bnk_17"),
    (0x38100035, "bnk_18"),
    (0x38200035, "bnk_19"),
    (0x382E0035, "bnk_20"),
]

# First, build a lookup of all table entries by manifest_id
print("Scanning for table entries...")
table_by_mid = {}

for bnk_pos, bnk_name in bnk_positions:
    region_start = max(0, bnk_pos - 0x20000)
    region_end = min(len(pak_data), bnk_pos + 0x50000)
    # Check ALL offsets (not just 40-aligned) since table might not be 40-aligned
    for offset in range(region_start, region_end):
        if offset + 40 > len(pak_data):
            break
        entry_data = pak_data[offset:offset+40]
        vals = [struct.unpack('<I', entry_data[i:i+4])[0] for i in range(0, 40, 4)]
        if vals[4] == 33555456 and vals[7] in (1, 9) and vals[8] == 0:
            mid = vals[5]
            if mid in known and mid not in table_by_mid:
                table_by_mid[mid] = (bnk_name, offset, vals)

print(f"Found {len(table_by_mid)} table entries for known manifest IDs")

# Now analyze
for mid, riff in known.items():
    if mid not in table_by_mid:
        continue
    bnk_name, table_offset, vals = table_by_mid[mid]
    v0, v1, v2, v3, v4, v5, v6, v7, v8, v9 = vals
    print(f"\n=== mid={mid}, riff=0x{riff:x} ===")
    print(f"Table in {bnk_name} region, table_offset=0x{table_offset:x}")
    for i, v in enumerate(vals):
        print(f"  v{i} = 0x{v:08x} ({v})")
    print(f"  v9 - bnk_pos = 0x{v9 - [p for p,n in bnk_positions if n==bnk_name][0]:x}")
    print(f"  riff - v3 = 0x{riff - v3:x}")
    print(f"  v9 + v3 - riff = 0x{v9 + v3 - riff:x}")
    print(f"  v1 + v3 - riff = 0x{v1 + v3 - riff:x}")