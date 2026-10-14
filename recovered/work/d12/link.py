from pathlib import Path
s=Path('work/d10/link.py').read_text().replace('work/d10/mounted.o','work/d12/memory.o').replace('work/d08/d08.bin','work/d11/d11.bin').replace('work/d10/linked.bin','work/d12/d12.bin').replace('work/d10/symbols.json','work/d12/symbols.json').replace('work/d10/ranges.json','work/d12/ranges.json')
s=s.replace("locations={'.mounted_update':(0x8ea0,0x90e0),'.mounted_end':(0x7770,0x78b0),'.poll':(0x1bd50,0x1c000),'.cancel':(0x7c78,0x7d5c)}","locations={'.memory':(0x8fc4,0x90e0),'.new_utility':(0x1bf08,0x1c000),'.event_name':(0x81b0,0x8280)}")
s=s.replace("'close_wheel':0x85d0","'close_wheel':0x85d0,'old_utility':0x7f94")
exec(s)
