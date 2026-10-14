import struct,json,shutil
from pathlib import Path
W=Path('work/d12');b=bytearray((W/'d12.bin').read_bytes());old=Path('work/d11/d11.bin').read_bytes();ranges=json.load(open(W/'ranges.json'))
for a,z in ranges:assert not any(old[a:z]),(hex(a),hex(z))
a=0x7fd4;struct.pack_into('<I',b,a,0x94000000|(((0x1bf08-a)//4)&0x3ffffff));ranges.append([a,a+4]);(W/'d12.bin').write_bytes(b);(W/'changes.json').write_text(json.dumps(ranges))
out=W/'build/Sage Selector D12';shutil.copytree('work/d11/build/Sage Selector D11',out,dirs_exist_ok=True);(out/'D11_TEST_NOTES.txt').unlink(missing_ok=True)
# Keep the native image unchanged; align the relocation table as requested by BNTX header alignment=4096.
import sys
sys.path.insert(0,'inputs/external-reference')
import zstandard as z
p=out/'romfs/UI/Tex/Icon/SageMemory.bntx.zs';v=bytearray(z.ZstdDecompressor().decompress(p.read_bytes()));r=struct.unpack_from('<I',v,0x18)[0];aligned=(r+4095)&~4095;pad=aligned-r
assert pad>0
v=v[:r]+bytes(pad)+v[r:];struct.pack_into('<II',v,0x18,aligned,len(v));struct.pack_into('<I',v,aligned+4,aligned);struct.pack_into('<Q',v,0xff8,aligned-0xff0);struct.pack_into('<I',v,aligned+0x34,aligned-0xff0);p.write_bytes(z.ZstdCompressor(level=19).compress(v));(W/'SageMemory.bntx').write_bytes(v)
print('Memory relocation alignment',hex(r),'->',hex(aligned))
