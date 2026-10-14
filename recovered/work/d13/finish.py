from pathlib import Path
import struct,json
p=Path('work/d13/d13.bin');b=bytearray(p.read_bytes());r=json.load(open('work/d13/ranges.json'))
struct.pack_into('<I',b,0xbd60,0x94000000|(((0x1bf18-0xbd60)//4)&0x3ffffff));r.append([0xbd60,0xbd64])
assert struct.unpack_from('<I',b,0x1dfac)[0]+0x1dfa0==0x59040
struct.pack_into('<I',b,0x1dfac,0x59050-0x1dfa0);r.append([0x1dfac,0x1dfb0])
p.write_bytes(b);Path('work/d13/changes.json').write_text(json.dumps(r))
