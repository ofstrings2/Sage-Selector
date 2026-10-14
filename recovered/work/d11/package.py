exec(open('work/decode_donors.py').read().split('D=Path')[0])
import zipfile
W=Path('work/d11');out=W/'build/Sage Selector D11';raw=(W/'d11.bin').read_bytes();base=(W/'d10.bin').read_bytes();h=bytearray((W/'baseline/Sage Selector D10/exefs/subsdk4').read_bytes()[:256]);body=bytearray()
end=max(b for a,b in json.load(open(W/'horse_ranges.json')));assert end<=0x1c000
struct.pack_into('<I',h,0x3c,struct.unpack_from('<I',h,0x3c)[0]+0x20)
for i in range(3):
 _,va,size=struct.unpack_from('<III',h,16+16*i)
 if i==0:size=end
 data=raw[va:va+size];c=lz4.block.compress(data,store_size=False,mode='high_compression',compression=12)
 struct.pack_into('<III',h,16+16*i,256+len(body),va,size);struct.pack_into('<I',h,96+i*4,len(c));h[160+32*i:192+32*i]=hashlib.sha256(data).digest();body.extend(c)
h[64:96]=hashlib.sha256(raw).digest();(out/'exefs/subsdk4').write_bytes(h+body)
allowed=json.load(open(W/'changes.json'));assert all(any(a<=i<b for a,b in allowed) for i,(x,y) in enumerate(zip(raw,base)) if x!=y)
# The mounted adapter, original wheel open/tick/close, Sage implementation and hook pools are unchanged.
for a,b in [(0x7770,0x78b0),(0x7c78,0x7cfc),(0x8ea0,0x90e0),(0x1bd50,0x1be44),(0x8280,0x8ea0),(0x90e0,0x9d80),(0x1bb98,0x1bd50),(0x2000,0x5000)]:assert raw[a:b]==base[a:b],(hex(a),hex(b))
notes='''Sage Selector D11 — TotK 1.2.1

Replace D10 with D11 in TKMM; do not enable both. Full replacement ZIP.

Changes:
- Horse now hands the live, on-foot whistle action back to the native game.
  Native animation, sound, horse notification, and completion are used.
- Warp displays the native Travel Medallion prototype inventory texture.
- Memory displays the native menu film-strip symbol, kept screen-upright.
- Horse displays the native shortcut horse-head symbol.
- Memory and Warp actions remain inactive, per the reduced scope.

Horse is available on foot. While mounted on Mineru it does nothing; it does
not force a whistle animation onto the rider or automatically dismount Link.
D10 mounted selector and native Mineru dismissal are preserved.

Test:
1. Toggle the five Sages and check mounted selector/dismissal still work.
2. Check the three icons, especially Memory upright and Warp visible.
3. On foot, select Horse and release Down: Link should whistle normally.
4. Tap Down to repeat Horse, then select a Sage and confirm normal toggling.
5. Repeat Horse after dismounting Mineru.

Local AArch64 tests passed using mock game services. Actual in-game whistle,
icon loading, and D11 regression behavior still require your test.
'''
(out/'D11_TEST_NOTES.txt').write_text(notes)
O=Path('outputs');O.mkdir(exist_ok=True);zp=O/'Sage Selector D11.zip'
with zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(out.rglob('*')):
  if p.is_file():z.write(p,str(p.relative_to(out.parent)))
with zipfile.ZipFile(zp) as z:assert z.testzip() is None
b=(out/'exefs/subsdk4').read_bytes()
for i in range(3):
 off,va,n=struct.unpack_from('<III',b,16+16*i);cs=struct.unpack_from('<I',b,96+4*i)[0];v=lz4.block.decompress(b[off:off+cs],uncompressed_size=n);assert v==raw[va:va+n];assert hashlib.sha256(v).digest()==b[160+32*i:192+32*i]
print('ZIP',zp,len(zp.read_bytes()),'sha256',hashlib.sha256(zp.read_bytes()).hexdigest())
(W/'verification.json').write_text(json.dumps({'zip':str(zp),'sha256':hashlib.sha256(zp.read_bytes()).hexdigest(),'text_end':hex(end),'baseline':json.load(open(W/'baseline.json')),'allowed_changes':allowed},indent=2))
