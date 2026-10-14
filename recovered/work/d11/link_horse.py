from pathlib import Path
s=Path('work/d10/link.py').read_text().replace("work/d10/mounted.o","work/d11/horse.o").replace("work/d08/d08.bin","work/d11/d10.bin").replace("work/d10/linked.bin","work/d11/horse_linked.bin").replace("work/d10/symbols.json","work/d11/horse_symbols.json").replace("work/d10/ranges.json","work/d11/horse_ranges.json")
s=s.replace("locations={'.mounted_update':(0x8ea0,0x90e0),'.mounted_end':(0x7770,0x78b0),'.poll':(0x1bd50,0x1c000),'.cancel':(0x7c78,0x7d5c)}","locations={'.utility':(0x7f94,0x8050),'.horse_begin':(0x8184,0x8280),'.horse_update':(0x1be44,0x1c000)}")
s=s.replace("'close_wheel':0x85d0","'close_wheel':0x85d0,'donor_begin':0x8280,'donor_update':0x90e0")
exec(s)
