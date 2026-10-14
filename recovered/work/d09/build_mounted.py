import json,hashlib,struct,zipfile
from pathlib import Path
W=Path('work/d09');O=Path('outputs');source=Path('inputs/external-reference')
baseline_sha=hashlib.sha256(source.read_bytes()).hexdigest();assert baseline_sha==json.loads(Path('work/d08/verification.json').read_text())['zip_sha256']
main=Path('inputs/exefs/main').read_bytes();assert hashlib.sha256(main).hexdigest()==json.loads(Path('work/decoded/vanilla.json').read_text())['sha256']
bid=main[64:96].hex().upper();addr=0x931bac;old=bytes.fromhex('2B0080D2');new=bytes.fromhex('2B0084D2');clean=Path('work/decoded/vanilla.bin').read_bytes();assert clean[addr:addr+4]==old
# Existing x11 mask: 0x0068000010000001. Add bit (RideRobot 25 - 12)=13.
assert (1|(0x1000<<16)|(0x68<<48))^(0x2001|(0x1000<<16)|(0x68<<48))==1<<13
ips=b'PATCH'+(addr+256).to_bytes(3,'big')+b'\0\4'+new+b'EOF'
assert ips[:5]==b'PATCH' and int.from_bytes(ips[5:8],'big')-256==addr and ips[10:14]==new and ips[14:]==b'EOF'
name='Sage Wheel v0.2 D09 Mounted Mineru';out=W/'build'/name;(out/'exefs').mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(source) as z:
 for entry in z.namelist():
  rel='/'.join(entry.split('/')[1:])
  if rel.startswith(('exefs/','romfs/')) and not entry.endswith('/'):
   p=out/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(entry))
(out/'exefs'/f'{bid}.ips').write_bytes(ips)
readme='''Sage Wheel v0.2 D09 — mounted Mineru diagnostic, TotK 1.2.1

Built from your confirmed working D08 ZIP. All four D08 game files are
byte-identical. One new build-ID-specific IPS changes the native whistle
eligibility mask to also permit the RideRobot action (25). No Player pack,
animation, UI, icon, or native Sage-call changes are included.

Replace D08 with D09 in TKMM; do not stack the iterations. Keep other test
conditions unchanged and rebuild/deploy. Disable original Emote Wheel and
Mineru Minus The Menu so their executables do not replace this baseline.

Test in order:
1. On foot: hold Down, choose a Sage, release, then tap to repeat.
2. Mount Mineru and hold Down. Confirm the wheel opens and pauses normally.
3. Select another Sage while mounted. Check Mineru remains controllable.
4. Open again and cancel. Check control returns without a frozen pose.
5. Select Mineru while mounted and release. Check normal dismount/dismissal,
   Link movement and camera, no lingering rider attachment, then resummon
   and remount Mineru to check the full cycle.
6. Repeat via a quick tap with Mineru remembered; test normal B dismount too.

D09 passed native eligibility-function host tests. In-game mounted opening
and clean rider teardown are NOT yet verified. If any step fails, report the
step and visible behavior; do not assume native cleanup completed.

Horse, Memory and Warp remain the D08 no-ops. After mounted use is verified,
implementation order remains Horse, then Memory #2, then native Warp or the
requested nearest-shrine alternative if warp-in-place is unsupported.
'''
(out/'D09_TEST_INSTRUCTIONS.txt').write_text(readme)
zpath=O/(name+'.zip')
with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(out.rglob('*')):
  if p.is_file():z.write(p,str(p.relative_to(out.parent)))
with zipfile.ZipFile(zpath) as z,zipfile.ZipFile(source) as a:
 assert z.testzip() is None
 for entry in a.namelist():
  rel='/'.join(entry.split('/')[1:])
  if rel.startswith(('exefs/','romfs/')) and not entry.endswith('/'):assert a.read(entry)==z.read(name+'/'+rel)
report={'baseline_sha256':baseline_sha,'zip_sha256':hashlib.sha256(zpath.read_bytes()).hexdigest(),'build_id':bid,'native_offset':hex(addr),'ips_offset':hex(addr+256),'old':old.hex(),'new':new.hex(),'ips_bytes':len(ips),'preserved_game_files':4}
(W/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
