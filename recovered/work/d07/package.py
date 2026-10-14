exec(open('work/decode_donors.py').read().split('D=Path')[0])
import zipfile
W=Path('work/d07');out=W/'build'/'Sage Wheel v0.1 D07 Emote Base';original=Path('work/donors/EmoteWheel');files=[p for p in original.rglob('*') if p.is_file()];changed=[str(p.relative_to(original)) for p in files if p.read_bytes()!=(out/p.relative_to(original)).read_bytes()];assert changed==['exefs/subsdk4'],changed
# Independently unpack rebuilt NSO, verify every segment hash and memory boundary.
b=(out/'exefs/subsdk4').read_bytes();mem=bytearray();segments=[]
for i in range(3):
 off,va,size=struct.unpack_from('<III',b,16+16*i);n=struct.unpack_from('<I',b,96+4*i)[0];d=lz4.block.decompress(b[off:off+n],uncompressed_size=size)
 assert hashlib.sha256(d).digest()==b[160+32*i:192+32*i]
 mem.extend(bytes(max(0,va+size-len(mem))));mem[va:va+size]=d;segments.append([va,size])
assert mem==(W/'d07.bin').read_bytes()
a=Path('work/decoded/emote.bin').read_bytes();assert mem[0x2000:0x5000]==a[0x2000:0x5000];assert mem[0x1c000:]==a[0x1c000:]
assert ((segments[0][1]+4095)&~4095)==0x1c000
assert b[0x3c:0x40]==(original/'exefs/subsdk4').read_bytes()[0x3c:0x40]
readme='''Sage Wheel v0.1 D07 Emote Base — TotK 1.2.1 diagnostic

Import this ZIP into TKMM and enable this iteration alone among Sage Wheel builds.
Disable original Emote Wheel and Mineru Minus The Menu. Keep the same other-mod
settings used for the D05 test so the comparison is useful.

Hold D-pad Down, select with the stick, and release normally.
Test TOP / Take The L first: it should toggle Tulin. Repeat to toggle back.
Then test right / Behold! (Yunobo), bottom-right / Empty Out Your Pockets
(Mineru), bottom / The Floss (Sidon), and left / Lucid Dreams (Riju).
Top-right, bottom-left, and top-left are harmless placeholders.
Test B cancellation and reopening the wheel after each selection.

All original donor names, icons, input, wheel, pause and animation resources
remain. The known Shinobi animation conflict has not been addressed here.
No Minus controls, utilities, new tap-repeat behavior or visual changes.

Audited against clean 1.2.1 main; actual injected ARM64 bytes passed 204 host
checks with mocked native services. This is not an in-game pass. Please report
save loading, wheel opening, exact position chosen, Sage response, and reopening.
'''
(out/'D07_TEST_INSTRUCTIONS.txt').write_text(readme)
O=Path('outputs');O.mkdir(exist_ok=True);zpath=O/'Sage Wheel v0.1 D07 Emote Base.zip'
with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(out.rglob('*')):
  if p.is_file():z.write(p,str(p.relative_to(out.parent)))
with zipfile.ZipFile(zpath) as z:
 assert z.testzip() is None
 for p in files:assert z.read(out.name+'/'+str(p.relative_to(original)))==(out/p.relative_to(original)).read_bytes()
report={'unchanged_game_files':len(files)-1,'game_files':len(files),'changed':changed,'segments':segments,'zip_sha256':hashlib.sha256(zpath.read_bytes()).hexdigest(),'subsdk_sha256':hashlib.sha256(b).hexdigest()}
(W/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
