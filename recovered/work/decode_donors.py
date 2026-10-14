import sys,struct,json,hashlib,re
from pathlib import Path
sys.path.insert(0,'vendor-python')
import lz4.block,capstone,ainb
D=Path('work/decoded');D.mkdir(exist_ok=True)
for name,path in [('vanilla','inputs/exefs/main'),('mineru','work/donors/Mineru Minus The Menu/exefs/main'),('emote','work/donors/EmoteWheel/exefs/subsdk4')]:
 b=Path(path).read_bytes(); flags=struct.unpack_from('<I',b,12)[0];segs=[];mem=bytearray()
 for i in range(3):
  off,va,size=struct.unpack_from('<III',b,16+16*i);cs=struct.unpack_from('<I',b,96+i*4)[0];raw=lz4.block.decompress(b[off:off+cs],uncompressed_size=size) if flags&(1<<i) else b[off:off+size];mem.extend(bytes(max(0,va+size-len(mem))));mem[va:va+size]=raw;segs.append([va,size]);(D/f'{name}.{i}.bin').write_bytes(raw)
 (D/f'{name}.bin').write_bytes(mem);(D/f'{name}.json').write_text(json.dumps({'segments':segs,'build_id':b[64:96].hex(),'sha256':hashlib.sha256(b).hexdigest()}));print(name,segs,b[64:96].hex())
 if name=='emote':
  (D/'emote.strings.txt').write_text('\n'.join(f'{m.start():08x} {m.group().decode()}' for m in re.finditer(rb'[ -~]{5,}',mem)))
  md=capstone.Cs(capstone.CS_ARCH_ARM64,capstone.CS_MODE_ARM);(D/'emote.asm').write_text('\n'.join(f'{x.address:08x} {x.mnemonic:8} {x.op_str}' for x in md.disasm(mem[:segs[0][1]],0)))
for label,base in [('vanilla',Path('inputs/romfs')),('mineru',Path('work/donors/Mineru Minus The Menu/romfs'))]:
 for f in ['Main','Pouch','Event']:
  p=base/f'Sequence/{f}.module.ainb';g=ainb.AINB.from_binary(p.read_bytes()).as_dict();(D/f'{label}.{f}.json').write_text(json.dumps(g,indent=2))
