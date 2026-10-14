from pathlib import Path
import struct,json
b=Path('work/d14/d14.bin').read_bytes();n=Path('work/d15/d15.bin').read_bytes();r=json.load(open('work/d15/ranges.json'))
assert not any(b[0x1e50:0x2000])
assert len(b)==len(n)
assert all(any(a<=i<z for a,z in r) for i,(x,y) in enumerate(zip(b,n)) if x!=y)
# The adjacent original initializer stores the trampoline base 0x2000;
# added helpers occupy only preceding alignment padding, never that page.
assert b[0x1e30:0x1e44].hex()=='01020090000000b000000091200000f9c0035fd6'
refs=[]
for pc in range(0,0x1bfe8,4):
 w=struct.unpack_from('<I',b,pc)[0]
 if w&0x7c000000==0x14000000:
  d=w&0x3ffffff;d=d-(1<<26) if d&(1<<25) else d
  if 0x1e50<=pc+4*d<0x2000:refs.append(pc)
assert not refs
Path('work/d15/changes.json').write_text(json.dumps(r))
print('PASS: only Sleep implementation and previously unused pre-trampoline padding differ; Memory, other utilities, input/UI, BSS and game data unchanged.')
