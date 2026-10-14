exec(open('work/decode_donors.py').read().split('D=Path')[0])
import zipfile
W=Path('work/d12');out=W/'build/Sage Selector D12';raw=(W/'d12.bin').read_bytes();base=Path('work/d11/d11.bin').read_bytes();h=bytearray(Path('work/d11/build/Sage Selector D11/exefs/subsdk4').read_bytes()[:256]);body=bytearray()

for junk in out.rglob('.DS_Store'):junk.unlink()
ranges=json.load(open(W/'changes.json'));assert all(any(a<=i<b for a,b in ranges) for i,(x,y) in enumerate(zip(raw,base)) if x!=y)
for i in range(3):
 _,va,size=struct.unpack_from('<III',h,16+16*i)
 if i==0:size=0x1bf18
 data=raw[va:va+size];packed=lz4.block.compress(data,store_size=False,mode='high_compression',compression=12)
 struct.pack_into('<III',h,16+16*i,256+len(body),va,size);struct.pack_into('<I',h,96+4*i,len(packed));h[160+32*i:192+32*i]=hashlib.sha256(data).digest();body.extend(packed)
h[64:96]=hashlib.sha256(raw).digest();(out/'exefs/subsdk4').write_bytes(h+body)
notes='''Sage Selector D12 — TotK 1.2.1

D11 plus ONE utility: Memory / The Awakening.

On foot, select Memory and release Down. D12 requests the game's dedicated
DmT_OP_GanonWakeUp_PreRender_Memory replay event directly, without opening
Adventure Log or the Memory list. Native event settings control playback
and returning Link to his original position. Tap Down repeats the selection.
Memory is inactive while mounted on Mineru; dismount before using it.

The Memory icon's relocation table is now aligned to its declared 4096-byte
file alignment. Its native pixels and existing upright rotation are unchanged.
The icon repair is a candidate fix and needs an in-game check.

Horse, Sage toggles, and mounted selector/dismissal retain D11 behavior.
Warp remains inactive. No new game resource files are added.

Install D12 INSTEAD OF D11; do not stack them.
Test: Memory icon -> Memory playback -> clean gameplay return -> Horse and
Sages -> mounted selector. Also test Memory after dismounting Mineru.

Local native-code tests used mocked game services. In-game event playback,
icon rendering, and clean return are not verified here.
'''
(out/'D12_TEST_NOTES.txt').write_text(notes)
zp=Path('outputs/Sage Selector D12.zip')
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
  old=Path('work/d11/build/Sage Selector D11')/p.relative_to(out)
  if p.read_bytes()!=old.read_bytes():changed.append(str(p.relative_to(out)))
assert sorted(changed)==['exefs/subsdk4','romfs/UI/Tex/Icon/SageMemory.bntx.zs']
(W/'verification.json').write_text(json.dumps({'zip_sha256':hashlib.sha256(zp.read_bytes()).hexdigest(),'changed_game_files':changed,'patch_ranges':ranges},indent=2));print(str(zp),zp.stat().st_size,'bytes; changed',changed)
