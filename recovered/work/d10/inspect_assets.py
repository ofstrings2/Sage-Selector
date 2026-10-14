exec(open('work/resources.py').read().split("f='UI/")[0])
import struct,re
b=Path('work/decoded/vanilla.bin').read_bytes()
for a in range(0x44509d0,0x4450b30,8):print(hex(a-0x44509d0),hex(struct.unpack_from('<Q',b,a)[0]))
for n in ['Obj_Warp','Obj_WarpDLC','Obj_WarpDLC_Prototype']:
 print('\nACTOR',n)
 for k,v in sarc(dec(R/f'Pack/Actor/{n}.pack.zs')).items():
  if any(x in k for x in ['ActorParam','Pouch','UI','Icon']):print(k,re.findall(rb'[ -~]{4,}',v))
