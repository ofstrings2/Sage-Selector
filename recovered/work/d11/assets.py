exec(open('work/resources.py').read().split("f='UI/")[0])
import re,struct,byml
W=Path('work/d11');a=sarc(dec(R/'UI/LayoutArchive/Common.Product.110.Nin_NX_NVN.blarc.zs'));(W/'ui_files.txt').write_text('\n'.join(a))
for k,v in a.items():
 if k.endswith('bntx'):
  (W/'common.bntx').write_bytes(v);print(k,len(v));n=struct.unpack_from('<I',v,0x24)[0];t=struct.unpack_from('<Q',v,0x28)[0];rows=[]
  for j in range(n):
   p=struct.unpack_from('<Q',v,t+8*j)[0];np=struct.unpack_from('<Q',v,p+0x60)[0];ln=struct.unpack_from('<H',v,np)[0];nm=v[np+2:np+2+ln].decode(errors='replace');rows.append([nm,p])
  (W/'texture_index.json').write_text(json.dumps(rows));print('textures',len(rows));print([r for r in rows if re.search('horse|memory|recollect|movie|warp|film',r[0],re.I)])
print('relevant layouts',[k for k in a if re.search('memory|recollect|challenge|horse|map',k,re.I) and k.endswith('bflyt')])
print(byml.Byml((R/'UI/AdventureMemorySetTable/AdventureMemorySetTable.game__ui__AdventureMemorySetTable.bgyml').read_bytes()).parse())
