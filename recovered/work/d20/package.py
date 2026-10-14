import hashlib,json,shutil,zipfile
from pathlib import Path

w=Path('work/d20')
base=Path('work/d19/build/Sage Selector D19')
out=w/'build/Sage Selector D20'
shutil.copytree(base,out)
for p in out.glob('*NOTES*'):p.unlink()
icon='romfs/UI/Tex/Icon/SageMemory.bntx.zs'
(out/icon).write_bytes((Path('work/d18/build/Sage Selector D18')/icon).read_bytes())
(out/'D20_TEST_NOTES.txt').write_text(
 'Sage Selector D20 — TotK 1.2.1\n'
 'Restores the exact working D18 Memory icon after D19 rendered it as a gray square.\n'
 'D19 executable, three-second auto-skip timing, Horse icon, Sleep label, and all other files are unchanged.\n'
 'Replace D19; do not stack builds.\n')
changed=[]
for p in out.rglob('*'):
 if p.is_file() and str(p.relative_to(out)).startswith(('exefs/','romfs/')):
  if p.read_bytes()!=(base/p.relative_to(out)).read_bytes():changed.append(str(p.relative_to(out)))
assert changed==[icon],changed
assert (out/'exefs/subsdk4').read_bytes()==(base/'exefs/subsdk4').read_bytes()
zp=Path('outputs/Sage Selector D20.zip')
with zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(out.rglob('*')):
  if p.is_file():z.write(p,str(p.relative_to(out.parent)))
with zipfile.ZipFile(zp) as z:assert z.testzip() is None
(w/'verification.json').write_text(json.dumps({'zip_sha256':hashlib.sha256(zp.read_bytes()).hexdigest(),'changed_vs_D19':changed,'memory_icon_identical_to_D18':True,'executable_identical_to_D19':True},indent=2))
print(zp,zp.stat().st_size,'bytes')
