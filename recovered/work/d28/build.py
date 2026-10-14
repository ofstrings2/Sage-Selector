"""D28: reduce only the D27 Horse artwork by exactly 1.5% about its center."""

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


root = Path('work/d28')
base = Path('work/d27/build/Sage Selector')
mod = root / 'build/Sage Selector'
output = Path('outputs/D28/Sage Selector.zip')
encoder = Path('work/d23/tools/bin/astcenc')
scale = 0.985
center = 71.5


def swizzle(linear):
    assert len(linear) == 36 * 36 * 16
    result = bytearray(0x9000)
    for y in range(36):
        for x in range(36 * 16):
            offset = ((y // 32) * 512 * 4 * 9 + (x // 64) * 512 * 4
                      + ((y % 32) // 8) * 512 + ((x % 64) // 32) * 256
                      + ((y % 8) // 2) * 64 + ((x % 32) // 16) * 32
                      + (y % 2) * 16 + x % 16)
            result[offset] = linear[y * 36 * 16 + x]
    return bytes(result)


shutil.rmtree(mod, ignore_errors=True)
shutil.copytree(base, mod)
(root / 'images').mkdir(parents=True, exist_ok=True)
source = Image.open('work/d27/images/SageHorse.png').convert('RGBA')
assert source.size == (144, 144)
inverse = 1.0 / scale
offset = center * (1.0 - inverse)
image = source.transform(
    (144, 144), Image.Transform.AFFINE,
    (inverse, 0.0, offset, 0.0, inverse, offset),
    resample=Image.Resampling.BICUBIC,
    fillcolor=(0, 0, 0, 0),
)
png = root / 'images/SageHorse.png'
astc = root / 'images/SageHorse.astc'
image.save(png)
subprocess.run(
    [str(encoder), '-cs', str(png), str(astc), '4x4', '-thorough', '-silent'],
    check=True,
)
encoded = astc.read_bytes()
assert encoded[:7] == bytes.fromhex('13aba15c040401')
path = mod / 'romfs/UI/Tex/Icon/SageHorse.bntx.zs'
before = bytearray(zstd.ZstdDecompressor().decompress(path.read_bytes()))
bntx = bytearray(before)
texture = struct.unpack_from('<Q', bntx, struct.unpack_from('<Q', bntx, 0x28)[0])[0]
assert struct.unpack_from('<I', bntx, texture + 0x1c)[0] == 0x2d06
assert struct.unpack_from('<II', bntx, texture + 0x24) == (144, 144)
bntx[0x1000:0xa000] = swizzle(encoded[16:])
assert bntx[:0x1000] == before[:0x1000]
assert bntx[0xa000:] == before[0xa000:]
path.write_bytes(zstd.ZstdCompressor(level=19).compress(bntx))
assert zstd.ZstdDecompressor().decompress(path.read_bytes()) == bntx

changed = sorted(
    str(member.relative_to(mod)) for member in mod.rglob('*')
    if member.is_file() and member.read_bytes() != (base / member.relative_to(mod)).read_bytes()
)
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

report = {
    'source': 'D27',
    'horse_scale': scale,
    'changed': changed,
    'other_files_byte_identical': True,
    'zip_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
}
(root / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(output, output.stat().st_size, report['zip_sha256'])
