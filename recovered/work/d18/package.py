import hashlib,json,shutil,struct,zipfile,sys
from pathlib import Path
sys.path.insert(0,'vendor-python')
import lz4.block

w=Path('work/d18')
old=Path('work/d17/build/Sage Selector D17')
out=w/'build/Sage Selector D18'
shutil.copytree(old,out,dirs_exist_ok=True)
for p in out.glob('*NOTES*'):p.unlink()

raw=(w/'d18.bin').read_bytes()
base=Path('work/d17/d17.bin').read_bytes()
ranges=json.loads((w/'changes.json').read_text())
assert len(raw)==len(base)
assert all(any(a<=i<b for a,b in ranges) for i,(x,y) in enumerate(zip(raw,base)) if x!=y)
h=bytearray((old/'exefs/subsdk4').read_bytes()[:256]);body=bytearray()
assert struct.unpack_from('<I',h,0x3c)[0]==0x188b8
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

(out/'D18_TEST_NOTES.txt').write_text(
 'Sage Selector D18 — TotK 1.2.1\n'
 'D17 auto-skip failed because it hooked the controller-style getter at subsdk4+0x1b990. D18 hooks the actual Npad state polls at 0x1ba00 (FullKey), 0x1b9d0 (Handheld), and 0x1b9b0 (JoyDual). It waits four seconds after the native Memory event becomes active, sends X then Plus, and retries up to twice while that same event is active. Native request/teardown and all other D17 behaviors are unchanged. In-game auto-skip remains unverified.\n'
 'Replace D17; do not stack builds.\n')

zp=Path('outputs/Sage Selector D18.zip')
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
assert changed==['exefs/subsdk4'],changed
(w/'verification.json').write_text(json.dumps({'zip_sha256':hashlib.sha256(zp.read_bytes()).hexdigest(),'changed_game_files':changed,'wrong_d17_hook':'controller style query','corrected_hooks':['FullKey NpadStates','Handheld NpadStates','JoyDual NpadStates'],'memory_auto_cancel_in_game_verified':False},indent=2))
print(zp,zp.stat().st_size,'bytes')
