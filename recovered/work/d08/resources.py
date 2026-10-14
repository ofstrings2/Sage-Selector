exec(open('work/resources.py').read().split("f='UI/")[0])
import struct,re
W=Path('work/d08');O=W/'build'/'Sage Wheel v0.2 D08'/'romfs';(O/'EmoteConfig').mkdir(parents=True,exist_ok=True)
positions=['Top','Top Right','Right','Down Right','Down','Down Left','Left','Top Left']
labels=['Tulin','Memory','Yunobo','Mineru','Sidon','Horse','Riju','Warp']
icons=['Obj_SageSoul_Rito','Obj_Photo_Other','Obj_SageSoul_Goron','Obj_SageSoul_Zonau','Obj_SageSoul_Zora','GameRomHorseSaddle_00','Obj_SageSoul_Gerudo','Obj_Warp']
old=json.loads((E/'EmoteConfig/wheel.json').read_text());ids=[old['slots'][x] for x in positions]
config={'emotes':{id:{'EmoteID':id,'ASCommand':'Wait','SLink':'Wait','Bntx':icon,'Name':name,'Loop':False,'DurationMs':1000,'MusicDelayMs':0} for id,icon,name in zip(ids,icons,labels)}}
(O/'EmoteConfig/emotes.json').write_text(json.dumps(config,indent=2)+'\n');(O/'EmoteConfig/wheel.json').write_text(json.dumps({'slots':dict(zip(positions,ids))},indent=2)+'\n')
evidence=[]
for label,icon in zip(labels,icons):
 p=R/'UI/Tex/Icon'/f'{icon}.bntx.zs';data=dec(p);assert data[:4]==b'BNTX' and data[0x20:0x24]==b'NX  '
 count=struct.unpack_from('<I',data,0x24)[0];table=struct.unpack_from('<Q',data,0x28)[0];tex=struct.unpack_from('<Q',data,table)[0];assert data[tex:tex+4]==b'BRTI'
 names=[m.group().decode() for m in re.finditer(rb'[A-Za-z0-9_]{5,}',data[:min(len(data),4096)]) if icon.encode() in m.group()]
 assert names,(icon,'Internal texture name absent')
 evidence.append({'slot':label,'path':str(p.relative_to(R)),'count':count,'internal_names':names,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(W/'native_icons.json').write_text(json.dumps(evidence,indent=2));print(json.dumps(evidence,indent=2))
# Byte-level field evidence for the Player override being removed.
a=sarc(dec(R/'Pack/Actor/Player.pack.zs'));b=sarc(dec(E/'Pack/Actor/Player.pack.zs'))
for k in a:
 if a[k]!=b.get(k):
  def strings(v):return set(x.group().decode(errors='replace') for x in re.finditer(rb'[ -~]{4,}',v))
  print(k,'added strings', sorted(strings(b[k])-strings(a[k])),'removed strings',sorted(strings(a[k])-strings(b[k])))
