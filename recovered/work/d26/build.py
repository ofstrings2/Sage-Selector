"""D26: make the complete Horse spur about 140 px wide, changing nothing else."""

import hashlib
import json
import shutil
import struct
import subprocess
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, 'vendor-python')
import zstandard as zstd
from PIL import Image

root = Path('work/d26')
base = Path('work/d25/build/Sage Selector')
mod = root / 'build/Sage Selector'
output = Path('outputs/D26/Sage Selector.zip')
encoder = Path('work/d23/tools/bin/astcenc')
shutil.rmtree(mod, ignore_errors=True)
shutil.copytree(base, mod)

root.joinpath('images').mkdir(parents=True, exist_ok=True)
source = Image.open('work/d23/images/SageHorse.png').convert('RGBA')
assert source.size == (144, 144)
enlarged = source.resize((148, 148), Image.Resampling.LANCZOS)
# The 2 px canvas crop removes transparent margin, not the spoke silhouettes.
image = enlarged.crop((2, 2, 146, 146))
assert image.size == (144, 144)
png = root / 'images/SageHorse.png'
image.save(png)
astc = root / 'SageHorse.astc'
subprocess.run([str(encoder), '-cs', str(png), str(astc), '4x4', '-thorough', '-silent'], check=True)
encoded = astc.read_bytes()
assert encoded[:7] == bytes.fromhex('13aba15c040401')
assert len(encoded[16:]) == 36 * 36 * 16

def swizzle(linear):
    result = bytearray(0x9000)
    for y in range(36):
        for x in range(36 * 16):
            offset = (y // 32) * 512 * 4 * 9 + (x // 64) * 512 * 4 + ((y % 32) // 8) * 512 + ((x % 64) // 32) * 256 + ((y % 8) // 2) * 64 + ((x % 32) // 16) * 32 + (y % 2) * 16 + x % 16
            result[offset] = linear[y * 36 * 16 + x]
    return bytes(result)

path = mod / 'romfs/UI/Tex/Icon/SageHorse.bntx.zs'
bntx = bytearray(zstd.ZstdDecompressor().decompress(path.read_bytes()))
texture = struct.unpack_from('<Q', bntx, struct.unpack_from('<Q', bntx, 0x28)[0])[0]
assert struct.unpack_from('<I', bntx, texture + 0x1c)[0] == 0x2d06
assert struct.unpack_from('<II', bntx, texture + 0x24) == (144, 144)
bntx[0x1000:0xa000] = swizzle(encoded[16:])
path.write_bytes(zstd.ZstdCompressor(level=19).compress(bntx))

changed = sorted(str(p.relative_to(mod)) for p in mod.rglob('*') if p.is_file() and p.read_bytes() != (base / p.relative_to(mod)).read_bytes())
assert changed == ['romfs/UI/Tex/Icon/SageHorse.bntx.zs']
assert not (mod / 'romfs/UI/LayoutArchive').exists()
output.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as package:
    for member in sorted(mod.rglob('*')):
        if member.is_file():
            package.write(member, str(member.relative_to(mod.parent)))
with zipfile.ZipFile(output) as package:
    assert package.testzip() is None
    assert len(package.namelist()) == 12
report = {'source':'D25', 'changed':changed, 'horse_art_scale_vs_D23':148/144,
          'other_files_byte_identical':True,
          'zip_sha256':hashlib.sha256(output.read_bytes()).hexdigest()}
(root / 'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(output,output.stat().st_size,report['zip_sha256'])
