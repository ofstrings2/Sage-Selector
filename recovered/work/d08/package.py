exec(open('work/decode_donors.py').read().split('D=Path')[0])
import zipfile
W=Path('work/d08');O=Path('outputs');out=W/'build'/'Sage Wheel v0.2 D08';donor=Path('work/donors/EmoteWheel')
donorfiles={str(p.relative_to(donor)):p for p in donor.rglob('*') if p.is_file()};gamefiles={str(p.relative_to(out)):p for d in ['exefs','romfs'] for p in (out/d).rglob('*') if p.is_file()}
assert set(gamefiles)=={'exefs/main.npdm','exefs/subsdk4','romfs/EmoteConfig/emotes.json','romfs/EmoteConfig/wheel.json'}
assert gamefiles['exefs/main.npdm'].read_bytes()==donorfiles['exefs/main.npdm'].read_bytes()
removed=sorted(set(donorfiles)-set(gamefiles));assert len(removed)==45
b=gamefiles['exefs/subsdk4'].read_bytes();expected=(W/'d08.bin').read_bytes();ranges=[]
for i in range(3):
 off,va,n=struct.unpack_from('<III',b,16+16*i);c=struct.unpack_from('<I',b,96+4*i)[0];d=lz4.block.decompress(b[off:off+c],uncompressed_size=n)
 assert d==expected[va:va+n] and hashlib.sha256(d).digest()==b[160+32*i:192+32*i]
 ranges.append([va,n])
assert ranges==[[0,0x1bd50],[0x1c000,26312],[0x23000,120792]]
old=(Path('work/d07/d07.bin')).read_bytes()
for a,z in [(0x78b0,0x7c78),(0x7d80,0x7eb0),(0x8050,0x8180),(0x8280,0x8ea0),(0x90e0,0x9d80),(0x2000,0x5000),(0x1c000,len(old))]:assert expected[a:z]==old[a:z],(hex(a),hex(z))
manifest='Sage Wheel D08 — exact package changes from D07 / original donor\n\nREMOVED GAME FILES (45)\n'+'\n'.join(removed)+'\n\nRETAINED GAME FILES\n'+'\n'.join(sorted(gamefiles))+'\n\nmain.npdm is unchanged. subsdk4 and both configuration files are updated.\nNative icons are referenced from the base game; no texture overrides are shipped.\n'
(out/'D08_RESOURCE_MANIFEST.txt').write_text(manifest)
readme='''Sage Wheel v0.2 D08 — TotK 1.2.1

Import this ZIP as the replacement for D07 in TKMM. Disable D07 and all other
Sage Wheel iterations, original Emote Wheel, and Mineru Minus The Menu.
Enable Shinobi for the compatibility test. Rebuild/deploy the TKMM output;
D07's removed animation files must not remain in the deployed mod.

Controls: hold D-pad Down for the donor's existing ~500ms threshold; select
with the right stick and release to activate once. A short tap then activates
the same selection once. B cancellation retains the previous selection.
Selection is remembered for the running session.

Clockwise from top: Tulin, Memory, Yunobo, Mineru, Sidon, Horse, Riju, Warp.
Memory/Horse/Warp remain no-ops. Native item icons are used for every slot.

Acceptance tests, in order:
1. Check Shinobi animations with D08 enabled.
2. Mount Mineru: normal Link pose, normal dismount, then try Sage Wheel while
   mounted. Mounted Down input remains subject to the game's native routing.
3. Hold Down, select Tulin, release: exactly one toggle.
4. Tap Down: Tulin toggles again, exactly once.
5. Select another Sage, release, then tap: both target that new Sage.
6. Test all five Sages ON and OFF; reopen and cancel the wheel.
7. Check all eight labels/icons and their positions.
8. Confirm Memory/Horse/Warp are no-ops on release and tap.

This build passed host execution tests with mocked game services. Shinobi,
Mineru mounted behavior and actual rendering still need in-game verification.
No Mineru-specific Vow changes, forced actor manipulation or Minus controls.
'''
(out/'D08_TEST_INSTRUCTIONS.txt').write_text(readme)
zpath=O/'Sage Wheel v0.2 D08.zip'
with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(out.rglob('*')):
  if p.is_file():z.write(p,str(p.relative_to(out.parent)))
with zipfile.ZipFile(zpath) as z:
 assert z.testzip() is None
 for rel,p in gamefiles.items():assert z.read(out.name+'/'+rel)==p.read_bytes()
report={'removed':removed,'retained':sorted(gamefiles),'zip_sha256':hashlib.sha256(zpath.read_bytes()).hexdigest(),'subsdk_sha256':hashlib.sha256(b).hexdigest(),'zip_bytes':zpath.stat().st_size,'segments':ranges}
(W/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['removed']},indent=2))
