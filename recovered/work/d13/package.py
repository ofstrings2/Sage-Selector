exec(open('work/decode_donors.py').read().split('D=Path')[0])
import shutil,zipfile
W=Path('work/d13');old=Path('work/d12/build/Sage Selector D12');out=W/'build/Sage Selector D13'
shutil.copytree(old,out,dirs_exist_ok=True)
for p in out.rglob('.DS_Store'):p.unlink()
for p in out.glob('*NOTES*'):p.unlink()
raw=(W/'d13.bin').read_bytes();base=Path('work/d12/d12.bin').read_bytes();ranges=json.load(open(W/'changes.json'))
assert len(raw)==len(base)
assert all(any(a<=i<b for a,b in ranges) for i,(x,y) in enumerate(zip(raw,base)) if x!=y)
h=bytearray((old/'exefs/subsdk4').read_bytes()[:256]);body=bytearray()
struct.pack_into('<I',h,0x3c,struct.unpack_from('<I',h,0x3c)[0]+0x10)
for i in range(3):
 _,va,size=struct.unpack_from('<III',h,16+16*i)
 if i==0:size=0x1bfd8
 data=raw[va:va+size];packed=lz4.block.compress(data,store_size=False,mode='high_compression',compression=12)
 struct.pack_into('<III',h,16+16*i,256+len(body),va,size);struct.pack_into('<I',h,96+4*i,len(packed));h[160+32*i:192+32*i]=hashlib.sha256(data).digest();body.extend(packed)
h[64:96]=hashlib.sha256(raw).digest();(out/'exefs/subsdk4').write_bytes(h+body)
(out/'D13_TEST_NOTES.txt').write_text('''Sage Selector D13 — TotK 1.2.1\n\nSelector-only HUD eligibility added: (Player actor flags at +0x28 & 0x1F800) == 0x1000, meaning pause reason 1 alone. The original GamePause/readiness/input checks remain, and any other actor pause reason cancels this fallback. Existing D12 wheel and action dispatcher reused. No actor flags or culling routines modified.\n\nInstall instead of D12. Native-code tests with mocked game services passed; SDC behavior needs in-game verification.\n''')
zp=Path('outputs/Sage Selector D13.zip')
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
