exec(open('work/resources.py').read().split("f='UI/")[0])
import struct,ainb
p=R/'Pack/Actor/Player.pack.zs';pack=sarc(dec(p));print([k for k in pack if 'ainb' in k])
for k,v in pack.items():
 if k.endswith('.ainb'):
  d=ainb.AINB.from_binary(v).as_dict();Path('work/d09/'+Path(k).name+'.json').write_text(json.dumps(d,indent=2))
  for n in d.get('Nodes',[]):
   if any(t.lower() in json.dumps(n).lower() for t in ['Whistle','RaumiGolem']): print(k,n.get('Node Index'),n.get('Name'))
