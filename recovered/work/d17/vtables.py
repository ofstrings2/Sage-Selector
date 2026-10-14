import json
r=json.load(open('work/d10/relocs.json'))
for target in [0x2867ab4,0x28849e4,0x2884ca4]:
 for k,v in r.items():
  if v==target:
   p=int(k);print('NAME',hex(target),'AT',hex(p));print([(hex(i-p),hex(r.get(str(i),0))) for i in range(p-0x80,p+0x98,8)])
