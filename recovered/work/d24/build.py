"""D24: tighten only the Sleep disc and Horse spokes from D23."""

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

root = Path('work/d24')
base = Path('work/d23/build/Sage Selector')
mod = root / 'build/Sage Selector'
output = Path('outputs/D24/Sage Selector.zip')
encoder = Path('work/d23/tools/bin/astcenc')
shutil.rmtree(mod, ignore_errors=True)
shutil.copytree(base, mod)
(root / 'images').mkdir(parents=True, exist_ok=True)

def centered_shrink(source, fraction):
    size = round(144 * fraction / 2) * 2
    image = Image.open(source).convert('RGBA').resize((size, size), Image.Resampling.LANCZOS)
    output_image = Image.new('RGBA', (144, 144), (0, 0, 0, 0))
    inset = (144 - size) // 2
    output_image.paste(image, (inset, inset))
    return output_image

def swizzle_astc(linear):
    assert len(linear) == 36 * 36 * 16
    block_height, pitch = 4, 9
    result = bytearray(0x9000)
    for y in range(36):
        for x in range(36 * 16):
            swizzled = (y // (8 * block_height)) * 512 * block_height * pitch + (x // 64) * 512 * block_height + ((y % (8 * block_height)) // 8) * 512 + ((x % 64) // 32) * 256 + ((y % 8) // 2) * 64 + ((x % 32) // 16) * 32 + (y % 2) * 16 + x % 16
            result[swizzled] = linear[y * 36 * 16 + x]
    return bytes(result)

fractions = {'SageHorse': 0.96, 'SageSleep': 0.82}
for name, fraction in fractions.items():
    image = centered_shrink(Path(f'work/d23/images/{name}.png'), fraction)
    png = root / 'images' / f'{name}.png'
    astc = root / 'images' / f'{name}.astc'
    image.save(png)
    subprocess.run([str(encoder), '-cs', str(png), str(astc), '4x4', '-thorough', '-silent'], check=True)
    encoded = astc.read_bytes()
    assert encoded[:7] == bytes.fromhex('13aba15c040401')
    path = mod / f'romfs/UI/Tex/Icon/{name}.bntx.zs'
    bntx = bytearray(zstd.ZstdDecompressor().decompress(path.read_bytes()))
    assert bntx[:4] == b'BNTX'
    texture = struct.unpack_from('<Q', bntx, struct.unpack_from('<Q', bntx, 0x28)[0])[0]
    assert struct.unpack_from('<I', bntx, texture + 0x1c)[0] == 0x2d06
    assert struct.unpack_from('<II', bntx, texture + 0x24) == (144, 144)
    bntx[0x1000:0xa000] = swizzle_astc(encoded[16:])
    path.write_bytes(zstd.ZstdCompressor(level=19).compress(bntx))

changed = sorted(str(p.relative_to(mod)) for p in mod.rglob('*') if p.is_file() and p.read_bytes() != (base / p.relative_to(mod)).read_bytes())
assert changed == ['romfs/UI/Tex/Icon/SageHorse.bntx.zs', 'romfs/UI/Tex/Icon/SageSleep.bntx.zs']
assert (mod / 'exefs/subsdk4').read_bytes() == (base / 'exefs/subsdk4').read_bytes()
assert not (mod / 'romfs/UI/LayoutArchive').exists()

output.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as package:
    for path in sorted(mod.rglob('*')):
        if path.is_file():
            package.write(path, str(path.relative_to(mod.parent)))
with zipfile.ZipFile(output) as package:
    assert package.testzip() is None
    assert len(package.namelist()) == 12

report = {'source': 'D23', 'changed': changed, 'sleep_scale_vs_D23': 0.82,
          'horse_scale_vs_D23': 0.96, 'other_files_byte_identical': True,
          'zip_sha256': hashlib.sha256(output.read_bytes()).hexdigest()}
(root / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(output, output.stat().st_size, report['zip_sha256'])
