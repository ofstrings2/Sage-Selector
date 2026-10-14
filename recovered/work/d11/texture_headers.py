exec(open('work/resources.py').read().split("f='UI/")[0])
import struct
b=Path('work/d11/common.bntx').read_bytes();idx=dict(json.loads(Path('work/d11/texture_index.json').read_text()))
for name in ['CategoryIconSh_Memory_140x140^s','MapIconHorse_66x66^w','Ds_ShortCutHorseIcon_01^s','Sd_MapWarpDLC_02^w']:
 p=idx[name];print(name,hex(p));print(' '.join('%x:%x'%(i,struct.unpack_from('<I',b,p+i)[0]) for i in range(0,0xa0,4)))
v=dec(R/'UI/Tex/Icon/Obj_WarpDLC_Prototype.bntx.zs');Path('work/d11/medallion.bntx').write_bytes(v);print('single header',v[:0x80].hex());p=struct.unpack_from('<Q',v,struct.unpack_from('<Q',v,0x28)[0])[0];print(hex(p),' '.join('%x:%x'%(i,struct.unpack_from('<I',v,p+i)[0]) for i in range(0,0xa0,4)))
