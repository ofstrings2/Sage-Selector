import hashlib,json,shutil,struct,zipfile,sys
from pathlib import Path
sys.path.insert(0,'vendor-python')
import lz4.block
import zstandard as zstd

w=Path('work/d17')
old=Path('work/d16/build/Sage Selector D16')
out=w/'build/Sage Selector D17'
shutil.copytree(old,out,dirs_exist_ok=True)
for p in out.glob('*NOTES*'):p.unlink()

raw=(w/'d17.bin').read_bytes()
base=Path('work/d16/d16.bin').read_bytes()
ranges=json.loads((w/'changes.json').read_text())
assert len(raw)==len(base)
assert all(any(a<=i<b for a,b in ranges) for i,(x,y) in enumerate(zip(raw,base)) if x!=y)
h=bytearray((old/'exefs/subsdk4').read_bytes()[:256]);body=bytearray()
assert struct.unpack_from('<I',h,0x3c)[0]==0x18878
struct.pack_into('<I',h,0x3c,0x188b8)
for i in range(3):
 _,va,size=struct.unpack_from('<III',h,16+16*i)
 if i==0:size=0x1bfe8
 data=raw[va:va+size]
 packed=lz4.block.compress(data,store_size=False,mode='high_compression',compression=12)
 struct.pack_into('<III',h,16+16*i,256+len(body),va,size)
 struct.pack_into('<I',h,96+4*i,len(packed))
 h[160+32*i:192+32*i]=hashlib.sha256(data).digest()
 body.extend(packed)
h[64:96]=hashlib.sha256(raw).digest()
(out/'exefs/subsdk4').write_bytes(h+body)

cfg_path=out/'romfs/EmoteConfig/emotes.json'
cfg=json.loads(cfg_path.read_text())
assert cfg['emotes']['warp']['Name']=='Warp'
cfg['emotes']['warp']['Name']='Sleep'
cfg_path.write_text(json.dumps(cfg,indent=2)+'\n')

# This is the exact ASTC texture from TotK's GameRomHorseReins_02; only its
# internal lookup name changes so the proven SageHorse slot can load it.
source=zstd.ZstdDecompressor().decompress((w/'GameRomHorseReins_02.bntx.zs').read_bytes())
icon=bytearray(source)
index=struct.unpack_from('<Q',icon,0x28)[0]
tex=struct.unpack_from('<Q',icon,index)[0]
name_ptr=struct.unpack_from('<Q',icon,tex+0x60)[0]
old_name=b'GameRomHorseReins_02'
assert icon[name_ptr+2:name_ptr+2+len(old_name)]==old_name
struct.pack_into('<H',icon,name_ptr,len('SageHorse'))
icon[name_ptr+2:name_ptr+2+len(old_name)]=b'SageHorse'+bytes(len(old_name)-len('SageHorse'))
assert source[0x1000:]==icon[0x1000:]
(out/'romfs/UI/Tex/Icon/SageHorse.bntx.zs').write_bytes(zstd.ZstdCompressor(level=19).compress(icon))

(out/'D17_TEST_NOTES.txt').write_text(
 'Sage Selector D17 — TotK 1.2.1\n'
 'Memory: after the existing native event request accepts, a scoped Npad input hook waits for the active event, then sends X followed by Plus. The hook stops injecting when the event ends or changes and times out after 20 seconds. It does not change the native request or teardown. The auto-cancel timing remains in-game unverified.\n'
 'Hold threshold: 500 ms -> 350 ms in both on-foot and mounted paths.\n'
 'Warp label: Sleep; slot identifier and behavior unchanged.\n'
 'Horse icon: native GameRomHorseReins_02 horse-face texture, original ASTC pixels; only internal BNTX lookup name changed to SageHorse.\n'
 'Replace D16; do not stack builds.\n')

zp=Path('outputs/Sage Selector D17.zip')
with zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
 for p in sorted(out.rglob('*')):
  if p.is_file():archive.write(p,str(p.relative_to(out.parent)))
with zipfile.ZipFile(zp) as archive:assert archive.testzip() is None
packed=(out/'exefs/subsdk4').read_bytes()
for i in range(3):
 off,va,size=struct.unpack_from('<III',packed,16+16*i)
 length=struct.unpack_from('<I',packed,96+4*i)[0]
 data=lz4.block.decompress(packed[off:off+length],uncompressed_size=size)
 assert data==raw[va:va+size]
 assert hashlib.sha256(data).digest()==packed[160+32*i:192+32*i]
changed=[]
for p in out.rglob('*'):
 if p.is_file() and str(p.relative_to(out)).startswith(('exefs/','romfs/')):
  if p.read_bytes()!=(old/p.relative_to(out)).read_bytes():changed.append(str(p.relative_to(out)))
assert changed==['exefs/subsdk4','romfs/EmoteConfig/emotes.json','romfs/UI/Tex/Icon/SageHorse.bntx.zs'],changed
(w/'verification.json').write_text(json.dumps({'zip_sha256':hashlib.sha256(zp.read_bytes()).hexdigest(),'changed_game_files':changed,'native_horse_source':'GameRomHorseReins_02','native_pixels_unchanged':True,'memory_auto_cancel_in_game_verified':False},indent=2))
print(zp,zp.stat().st_size,'bytes')
