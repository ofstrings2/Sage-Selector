"""D27: uniformly reduce the eight D26 icon artworks within their own canvases."""

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


root = Path('work/d27')
base = Path('work/d26/build/Sage Selector')
mod = root / 'build/Sage Selector'
output = Path('outputs/D27/Sage Selector.zip')
encoder = Path('work/d23/tools/bin/astcenc')
names = (
    'SageTulin', 'SageMemory', 'SageYunobo', 'SageMineru',
    'SageSidon', 'SageHorse', 'SageRiju', 'SageSleep',
)
size = 138  # 138/144 = 0.9583, a uniform 4.17% reduction.


def source_image(name):
    if name == 'SageHorse':
        path = Path('work/d26/images/SageHorse.png')
    elif name == 'SageSleep':
        path = Path('work/d25/candidates/F.png')
    else:
        path = Path('work/d23/images') / f'{name}.png'
    image = Image.open(path).convert('RGBA')
    assert image.size == (144, 144), path
    return image


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

for name in names:
    reduced = source_image(name).resize((size, size), Image.Resampling.LANCZOS)
    image = Image.new('RGBA', (144, 144), (0, 0, 0, 0))
    image.paste(reduced, ((144 - size) // 2, (144 - size) // 2))
    png = root / 'images' / f'{name}.png'
    astc = root / 'images' / f'{name}.astc'
    image.save(png)
    subprocess.run(
        [str(encoder), '-cs', str(png), str(astc), '4x4', '-thorough', '-silent'],
        check=True,
    )
    encoded = astc.read_bytes()
    assert encoded[:7] == bytes.fromhex('13aba15c040401')
    path = mod / f'romfs/UI/Tex/Icon/{name}.bntx.zs'
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
    str(path.relative_to(mod)) for path in mod.rglob('*')
    if path.is_file() and path.read_bytes() != (base / path.relative_to(mod)).read_bytes()
)
assert changed == sorted(f'romfs/UI/Tex/Icon/{name}.bntx.zs' for name in names)
assert not (mod / 'romfs/UI/LayoutArchive').exists()
assert not (mod / 'romfs/System').exists()

output.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as package:
    for path in sorted(mod.rglob('*')):
        if path.is_file():
            package.write(path, str(path.relative_to(mod.parent)))
with zipfile.ZipFile(output) as package:
    assert package.testzip() is None
    assert len(package.namelist()) == 12

report = {
    'source': 'D26',
    'scale': size / 144,
    'changed': changed,
    'non_icon_files_byte_identical': True,
    'zip_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
}
(root / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(output, output.stat().st_size, report['zip_sha256'])
