import struct
from pathlib import Path
b=Path('work/decoded/vanilla.bin').read_bytes();mod=struct.unpack_from('<I',b,4)[0];print('MOD',hex(mod),b[mod:mod+28].hex());dyn=mod+struct.unpack_from('<i',b,mod+4)[0];d={}
while True:
 t,v=struct.unpack_from('<QQ',b,dyn);dyn+=16
 if not t:break
 d[t]=v
print({hex(k):hex(v) for k,v in d.items()})
rels={}
for p in range(d[7],d[7]+d[8],24):
 a,t,v=struct.unpack_from('<QQq',b,p);rels[a]=v
for a in range(0x44509d0,0x4450b30,8):print(hex(a-0x44509d0),hex(rels.get(a,0)))
Path('work/d10/relocs.json').write_text(__import__('json').dumps(rels))
