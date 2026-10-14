exec(open('work/decode_donors.py').read().split('D=Path')[0])
import shutil,zipfile
W=Path('work/d16');old=Path('work/d15/build/Sage Selector D15');out=W/'build/Sage Selector D16'
shutil.copytree(old,out,dirs_exist_ok=True)
for p in out.rglob('.DS_Store'):p.unlink()
for p in out.glob('*NOTES*'):p.unlink()
raw=(W/'d16.bin').read_bytes();base=Path('work/d15/d15.bin').read_bytes();ranges=json.load(open(W/'changes.json'))
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
(out/'D16_TEST_NOTES.txt').write_text("Sage Selector D16 — TotK 1.2.1\n\nFix: retire the cached mounted-node veto (subsdk4+0x59008) when a live on-foot Whistle action begins, before the existing native AS/context reacquisition. Both Horse and Memory previously tested this persistent pointer as if it proved current mounting; only a matching mounted-end callback cleared it. A lost end callback therefore blocks both utilities despite a fresh player/action context. This mod BSS is not save data; reloading a save does not reinitialize it, whereas restarting the executable does.\n\nOnly the on-foot begin adapter at 0x8184..0x819B changes (24-byte region). Existing Horse ACTIVE/REQUEST reset and native begin forwarding remain. Native Memory request/teardown, Sleep toggle, mounted callbacks, R1 fallback, Sage dispatcher, input/UI, icons and data are byte-identical to D15. No global event or pause flags are cleared.\n\nEvidence: user reports Sages working and Horse/Memory failing after SDC; Sleep and gesture matrix were not observed in that game state. Local injected-stale-node tests reproduce Sages working, Horse/Memory failing, Sleep dispatch working, and tap/hold selection still functioning. D16 restores Horse/Memory in both gesture paths. Sixty-four repeated injected handoffs pass without reinitializing selector BSS; full Sleep and R1 regression tests pass. Native services/UI creation are mocked.\n\nThe exact SDC -> reason-1 cull -> Memory uncull -> immediate remount sequence has NOT been reproduced here: no running game/emulator is available. The diagnosis is a demonstrated stale-veto defect, not a confirmed capture of your game state. In-game acceptance remains pending for Sages, Horse, Memory, Sleep, tap, and hold/open/select/release. Replace D15; do not stack builds.\n")
zp=Path('outputs/Sage Selector D16.zip')
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
