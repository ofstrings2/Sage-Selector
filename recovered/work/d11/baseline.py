exec(open('work/decode_donors.py').read().split('D=Path')[0])
import zipfile
W=Path('work/d11');src=Path('inputs/Sage Selector D10.zip')
with zipfile.ZipFile(src) as z:z.extractall(W/'baseline')
b=(W/'baseline/Sage Selector D10/exefs/subsdk4').read_bytes();mem=bytearray();segs=[]
for i in range(3):
 off,va,size=struct.unpack_from('<III',b,16+16*i);cs=struct.unpack_from('<I',b,96+i*4)[0];v=lz4.block.decompress(b[off:off+cs],uncompressed_size=size);mem.extend(bytes(max(0,va+size-len(mem))));mem[va:va+size]=v;segs.append([va,size])
(W/'d10.bin').write_bytes(mem);(W/'baseline.json').write_text(json.dumps({'zip_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'segments':segs}))
md=capstone.Cs(capstone.CS_ARCH_ARM64,capstone.CS_MODE_ARM);(W/'d10.asm').write_text('\n'.join(f'{i.address:08x} {i.mnemonic:8} {i.op_str}' for i in md.disasm(mem[:segs[0][1]],0)))
print('segments',segs,'changes from localD08',sum(a!=b for a,b in zip(mem,Path('work/d08/d08.bin').read_bytes())))
