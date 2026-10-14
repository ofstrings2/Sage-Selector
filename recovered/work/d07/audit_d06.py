import sys,struct,json,hashlib,zipfile
from pathlib import Path
sys.path.insert(0,'vendor-python')
import lz4.block,capstone
W=Path('work/d07');D=next((W/'d06').iterdir());E=Path('work/donors/EmoteWheel');diff=[]
for p in D.rglob('*'):
 if not p.is_file():continue
 rel=p.relative_to(D);q=E/rel
 if not q.exists() or p.read_bytes()!=q.read_bytes():diff.append(str(rel))
print('changed files',diff)
b=(D/'exefs/subsdk4').read_bytes();flags=struct.unpack_from('<I',b,12)[0];mem=bytearray();segs=[]
for i in range(3):
 off,va,size=struct.unpack_from('<III',b,16+16*i);cs=struct.unpack_from('<I',b,96+i*4)[0];raw=lz4.block.decompress(b[off:off+cs],uncompressed_size=size) if flags&(1<<i) else b[off:off+size];mem.extend(bytes(max(0,va+size-len(mem))));mem[va:va+size]=raw;segs.append([va,size])
(W/'d06.bin').write_bytes(mem);print('segments',segs)
a=Path('work/decoded/emote.bin').read_bytes();ranges=[]
for i in range(0,max(len(a),len(mem)),4):
 if a[i:i+4]!=mem[i:i+4]:
  if ranges and ranges[-1][1]==i:ranges[-1][1]=i+4
  else:ranges.append([i,i+4])
print('word diff ranges',[(hex(x),hex(y)) for x,y in ranges]);(W/'d06_diff.json').write_text(json.dumps({'files':diff,'ranges':ranges,'segments':segs},indent=2))
md=capstone.Cs(capstone.CS_ARCH_ARM64,capstone.CS_MODE_ARM);md.skipdata=True
(W/'d06.asm').write_text('\n'.join(f'{x.address:08x} {x.mnemonic:8} {x.op_str}' for x in md.disasm(mem[:segs[0][1]],0)))
for x,y in ranges:
 if x<segs[0][1]:
  print('\nCHANGE',hex(x),hex(y));print('\n'.join(f'{i.address:08x} {i.mnemonic:8} {i.op_str}' for i in md.disasm(mem[x:y],x)))
