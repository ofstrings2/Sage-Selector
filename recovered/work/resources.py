import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,'tools')
from pack_utils import sarc
import zstandard as z
R=Path('inputs/romfs');E=Path('work/donors/EmoteWheel/romfs');out=Path('work/resources');out.mkdir(exist_ok=True)
dicts={}
for v in sarc(z.ZstdDecompressor().decompress((R/'Pack/ZsDic.pack.zs').read_bytes())).values():
 d=z.ZstdCompressionDict(v);dicts[d.dict_id()]=d
def dec(p):
 b=p.read_bytes();return z.ZstdDecompressor(dict_data=dicts.get(z.get_frame_parameters(b).dict_id)).decompress(b)
f='UI/LayoutArchive/Common.Product.110.Nin_NX_NVN.blarc.zs'
a=sarc(dec(R/f));b=sarc(dec(E/f));changes=[]
for k in sorted(a.keys()|b.keys()):
 if a.get(k)!=b.get(k):
  changes.append([k,len(a.get(k,b'')),len(b.get(k,b''))]);p=out/k;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b.get(k,b''))
print('UI changes',changes);(out/'ui_diff.json').write_text(json.dumps(changes,indent=2))
for p in E.rglob('*'):
 if not p.is_file():continue
 v=R/p.relative_to(E)
 print(p.relative_to(E), 'added' if not v.exists() else 'identical' if v.read_bytes()==p.read_bytes() else 'changed')
print('vow textures', [p.name for p in (R/'UI/Tex/Icon').glob('*') if any(s in p.name.lower() for s in ['sage','soul','companion'])])
