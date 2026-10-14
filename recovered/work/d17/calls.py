import struct,sys
from pathlib import Path
b=Path('work/decoded/vanilla.0.bin').read_bytes();target=int(sys.argv[1],16);hits=[]
for off in range(0,len(b),4):
 w=struct.unpack_from('<I',b,off)[0]
 if w&0x7c000000==0x14000000:
  d=w&0x3ffffff;d=d-(1<<26) if d&(1<<25) else d
  if off+d*4==target:hits.append(hex(off))
print(hits)
