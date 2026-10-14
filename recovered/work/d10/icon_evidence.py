exec(open('work/resources.py').read().split("f='UI/")[0])
import re
for n in ['Obj_WarpDLC','Obj_WarpDLC_Prototype']:
 for k,v in sarc(dec(R/f'Pack/Actor/{n}.pack.zs')).items():
  if 'GameParameter' in k or 'Icon' in k:print(k,re.findall(rb'[ -~]{4,}',v))
