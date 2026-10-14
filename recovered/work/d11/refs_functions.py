import struct
from pathlib import Path
b=Path('work/decoded/vanilla.0.bin').read_bytes();ws=struct.unpack('<%dI'%(len(b)//4),b);targets={0x1b1e4cc,0x1b1e4f8,0x19e2b00}
for j,w in enumerate(ws):
 if w&0xfc000000 not in (0x94000000,0x14000000):continue
 imm=w&0x3ffffff;imm=imm-(1<<26) if imm&(1<<25) else imm;t=j*4+imm*4
 if t in targets and (t!=0x19e2b00 or 0x19a0000<j*4<0x1bf0000):print(hex(j*4),'->',hex(t))
