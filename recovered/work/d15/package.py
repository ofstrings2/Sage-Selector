exec(open('work/decode_donors.py').read().split('D=Path')[0])
import shutil,zipfile
W=Path('work/d15');old=Path('work/d14/build/Sage Selector D14');out=W/'build/Sage Selector D15'
shutil.copytree(old,out,dirs_exist_ok=True)
for p in out.rglob('.DS_Store'):p.unlink()
for p in out.glob('*NOTES*'):p.unlink()
raw=(W/'d15.bin').read_bytes();base=Path('work/d14/d14.bin').read_bytes();ranges=json.load(open(W/'changes.json'))
assert len(raw)==len(base)
assert all(any(a<=i<b for a,b in ranges) for i,(x,y) in enumerate(zip(raw,base)) if x!=y)
h=bytearray((old/'exefs/subsdk4').read_bytes()[:256]);body=bytearray()
# BSS unchanged from D13.
for i in range(3):
 _,va,size=struct.unpack_from('<III',h,16+16*i)
 if i==0:size=0x1bfe8
 data=raw[va:va+size];packed=lz4.block.compress(data,store_size=False,mode='high_compression',compression=12)
 struct.pack_into('<III',h,16+16*i,256+len(body),va,size);struct.pack_into('<I',h,96+4*i,len(packed));h[160+32*i:192+32*i]=hashlib.sha256(data).digest();body.extend(packed)
h[64:96]=hashlib.sha256(raw).digest();(out/'exefs/subsdk4').write_bytes(h+body)
(out/'D15_TEST_NOTES.txt').write_text("Sage Selector D15 — TotK 1.2.1\n\nSleep-only change: inspect the same eight equipped dynamic actor links (EquipmentUser + 0x20, stride 0x18, slots 0-7). Skip empty/invalid links and lifecycle states outside native sleep support (1-6).\n\nNative sleep-reason field: u32 at actor + 0x28, mask 0x7FF. Snapshot current actors on each activation. ANY nonzero sleep-reason field -> request native wake for ALL current actors; otherwise request native sleep for ALL. No persistent toggle state.\n\nSleep call unchanged: main+0x83AC04(actor, 0). D14 had no wake call; D15 adds its native mask-based counterpart main+0xAEDC50(actor, 0x7FF, zero-initialized native wake parameters). No culling/pause bits are manually changed.\n\nLocal AArch64 execution tests with mocked sleep/wake services passed, including 6,561 empty/awake/asleep combinations and an added awake item while another sleeps. D14 regression and reason-1 tests passed. In-game verification pending. Replace D14; do not stack builds. Memory and all other features are byte-identical outside the Sleep code.\n")
zp=Path('outputs/Sage Selector D15.zip')
with zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(out.rglob('*')):
  if p.is_file():z.write(p,str(p.relative_to(out.parent)))
with zipfile.ZipFile(zp) as z:assert z.testzip() is None
b=(out/'exefs/subsdk4').read_bytes()
for i in range(3):
 off,va,n=struct.unpack_from('<III',b,16+16*i);cs=struct.unpack_from('<I',b,96+4*i)[0];v=lz4.block.decompress(b[off:off+cs],uncompressed_size=n);assert v==raw[va:va+n];assert hashlib.sha256(v).digest()==b[160+32*i:192+32*i]
changed=[]
for p in out.rglob('*'):
 if p.is_file() and str(p.relative_to(out)).startswith(('exefs/','romfs/')):
  if p.read_bytes()!=(old/p.relative_to(out)).read_bytes():changed.append(str(p.relative_to(out)))
assert changed==['exefs/subsdk4']
(W/'verification.json').write_text(json.dumps({'zip_sha256':hashlib.sha256(zp.read_bytes()).hexdigest(),'changed_game_files':changed,'patch_ranges':ranges,'in_game_verified':False},indent=2))
print(zp,zp.stat().st_size,'bytes; only subsdk4 changed')
