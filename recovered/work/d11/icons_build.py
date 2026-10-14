exec(open('work/resources.py').read().split("f='UI/")[0])
import struct,shutil
W=Path('work/d11');out=W/'build/Sage Selector D11';shutil.copytree(W/'baseline/Sage Selector D10',out,dirs_exist_ok=True)
(out/'D10_TEST_NOTES.txt').unlink(missing_ok=True)
ar=(W/'common.bntx').read_bytes();idx=dict(json.loads((W/'texture_index.json').read_text()));template=(W/'medallion.bntx').read_bytes()
def extract(n,new):
 p=idx[n];size=struct.unpack_from('<I',ar,p+0x50)[0];table=struct.unpack_from('<Q',ar,p+0x70)[0];data=struct.unpack_from('<Q',ar,table)[0]
 b=bytearray(template[:0x1000]);b.extend(ar[data:data+size]);rlt=bytearray(template[0xb000:]);off=len(b)
 struct.pack_into('<I',rlt,4,off);struct.pack_into('<I',rlt,0x34,size+16);b.extend(rlt)
 struct.pack_into('<II',b,0x18,off,len(b));struct.pack_into('<Q',b,0xff8,size+16)
 b[0x1f8+0x10:0x1f8+0x60]=ar[p+0x10:p+0x60]
 struct.pack_into('<H',b,0x1b8,len(new));b[0x1ba:0x1d0]=new.encode()+bytes(0x16-len(new))
 assert struct.unpack_from('<Q',b,0x498)[0]==0x1000
 path=out/'romfs/UI/Tex/Icon'/f'{new}.bntx.zs';path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(z.ZstdCompressor(level=19).compress(b));(W/f'{new}.bntx').write_bytes(b)
 return {'source_texture':n,'source_archive':'UI/LayoutArchive/Common.Product.110.Nin_NX_NVN.blarc.zs','output':str(path.relative_to(out)),'compressed_pixels_unchanged':True,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
records=[extract('Nt_PauseIconCh_00^s','SageMemory'),extract('Ds_ShortCutHorseIcon_01^s','SageHorse')]
p=out/'romfs/EmoteConfig/emotes.json';cfg=json.loads(p.read_text());cfg['emotes']['warp']['Bntx']='Obj_WarpDLC_Prototype';cfg['emotes']['memory']['Bntx']='SageMemory';cfg['emotes']['horse']['Bntx']='SageHorse';p.write_text(json.dumps(cfg,indent=2)+'\n')
records.append({'slot':'Warp','source_texture':'UI/Tex/Icon/Obj_WarpDLC_Prototype.bntx.zs','standalone_native':True})
(W/'icon_evidence.json').write_text(json.dumps(records,indent=2));print(records)
