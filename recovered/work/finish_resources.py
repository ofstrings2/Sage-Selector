import sys,struct,json,zlib
from pathlib import Path
sys.path.insert(0,'vendor-python')
import zstandard as z
R=Path('inputs/romfs');O=Path('work/build/Sage Wheel v0.1 D02/romfs');path='System/Resource/ResourceSizeTable.Product.121.rsizetable.zs';raw=bytearray(z.ZstdDecompressor().decompress((R/path).read_bytes()));assert raw[:6]==b'RESTBL';v,sl,nc,nn=struct.unpack_from('<4I',raw,6);h=zlib.crc32(b'Sequence/Main.module.ainb');found=False
for i in range(nc):
 off=22+8*i;key,old=struct.unpack_from('<II',raw,off)
 if key==h:
  new=old+65536;struct.pack_into('<I',raw,off+4,new);found=True;break
assert found
p=O/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.ZstdCompressor(level=10).compress(raw));Path('work/rst_change.json').write_text(json.dumps({'path':'Sequence/Main.module.ainb','crc32':hex(h),'old_allocation':old,'new_allocation':new,'reason':'Conservative 64 KiB headroom for four added sequence nodes and their runtime graph metadata; every other entry unchanged'},indent=2));print(old,new)
