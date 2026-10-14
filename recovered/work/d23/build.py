"""D23: Sage Selector-only icon textures; leave the shared ability layout untouched."""

import hashlib
import json
import math
import shutil
import struct
import subprocess
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, 'vendor-python')
sys.path.insert(0, 'work/d11/vendor')
import texture2ddecoder
import zstandard as zstd
from PIL import Image, ImageChops

root = Path('work/d23')
baseline = Path('work/d21/build/Sage Selector')
mod = root / 'build/Sage Selector'
romfs = Path('inputs/romfs')
encoder = root / 'tools/bin/astcenc'
output = Path('outputs/D23/Sage Selector.zip')
shutil.rmtree(mod, ignore_errors=True)
shutil.copytree(baseline, mod)
(root / 'images').mkdir(parents=True, exist_ok=True)

def decode_icon(name):
    raw = zstd.ZstdDecompressor().decompress((romfs / f'UI/Tex/Icon/{name}.bntx.zs').read_bytes())
    texture = struct.unpack_from('<Q', raw, struct.unpack_from('<Q', raw, 0x28)[0])[0]
    fmt = struct.unpack_from('<I', raw, texture + 0x1c)[0]
    width, height = struct.unpack_from('<II', raw, texture + 0x24)
    block_height = 1 << (struct.unpack_from('<I', raw, texture + 0x34)[0] & 7)
    table = struct.unpack_from('<Q', raw, texture + 0x70)[0]
    data = struct.unpack_from('<Q', raw, table)[0]
    block_bytes = {0x1d01: 8, 0x2d06: 16}[fmt]
    block_w, block_h = (width + 3) // 4, (height + 3) // 4
    pitch = (block_w * block_bytes + 63) // 64
    linear = bytearray(block_w * block_h * block_bytes)
    for y in range(block_h):
        for x in range(block_w * block_bytes):
            swizzled = (y // (8 * block_height)) * 512 * block_height * pitch + (x // 64) * 512 * block_height + ((y % (8 * block_height)) // 8) * 512 + ((x % 64) // 32) * 256 + ((y % 8) // 2) * 64 + ((x % 32) // 16) * 32 + (y % 2) * 16 + x % 16
            linear[y * block_w * block_bytes + x] = raw[data + swizzled]
    pixels = (texture2ddecoder.decode_bc4(bytes(linear), width, height)
              if fmt == 0x1d01 else texture2ddecoder.decode_astc(bytes(linear), width, height, 4, 4))
    image = Image.frombytes('RGBA', (width, height), pixels, 'raw', 'BGRA')
    if fmt == 0x1d01:
        alpha = image.getchannel('R')
        image = Image.new('RGBA', (width, height), 'white')
        image.putalpha(alpha)
    return image

def crop_resize(image, box):
    return image.crop(box).resize((144, 144), Image.Resampling.LANCZOS)

def tinted_mask(image, color):
    result = Image.new('RGBA', image.size, color)
    result.putalpha(image.getchannel('A'))
    return result

icons = {}
sage_sources = {
    'SageTulin': 'Obj_SageSoul_Rito',
    'SageYunobo': 'Obj_SageSoul_Goron',
    'SageMineru': 'Obj_SageSoul_Zonau',
    'SageSidon': 'Obj_SageSoul_Zora',
    'SageRiju': 'Obj_SageSoul_Gerudo',
}
for target, source in sage_sources.items():
    native = decode_icon(source)
    assert native.size == (144, 144)
    # The native 125 px colored Vow fills about 141 px after this 12.5% art
    # enlargement. The shared ability-wheel pane is never altered.
    large = native.resize((162, 162), Image.Resampling.LANCZOS)
    icons[target] = large.crop((9, 9, 153, 153))

# These are the requested *native* masks. Encode their color into independent
# ASTC textures: the game's shared icon material otherwise renders BC4 white.
horse = tinted_mask(Image.open('work/d22/Horse.png'), '#CAB52D')
memory = tinted_mask(Image.open('work/d22/Memory.png'), '#FFFCC6')
assert horse.size == (124, 124) and memory.size == (96, 96)
icons['SageHorse'] = crop_resize(horse, (8, 10, 112, 114))
icons['SageMemory'] = crop_resize(memory, (16, 8, 80, 72))

# Keep the medallion's own circular center, discarding the large diamond around
# it. This grows its visible circle to the same ~140 px core as the Vows.
sleep = decode_icon('Obj_WarpDLC_Prototype').crop((35, 35, 115, 115))
radial = Image.new('L', sleep.size)
radial.putdata([
    round(255 * max(0.0, min(1.0, (40.0 - math.hypot(x - 39.5, y - 39.5)) / 2.0)))
    for y in range(80) for x in range(80)
])
sleep.putalpha(ImageChops.multiply(sleep.getchannel('A'), radial))
icons['SageSleep'] = sleep.resize((144, 144), Image.Resampling.LANCZOS)

template = zstd.ZstdDecompressor().decompress((romfs / 'UI/Tex/Icon/Obj_SageSoul_Rito.bntx.zs').read_bytes())
texture = struct.unpack_from('<Q', template, struct.unpack_from('<Q', template, 0x28)[0])[0]
assert texture == 0x1f8
assert struct.unpack_from('<I', template, texture + 0x1c)[0] == 0x2d06
assert struct.unpack_from('<II', template, texture + 0x24) == (144, 144)
assert struct.unpack_from('<I', template, texture + 0x50)[0] == 0x9000
assert template[0xa000:0xa004] == b'_RLT'

def swizzle_astc(linear):
    block_w = block_h = 36
    block_height = 4
    pitch = 9
    result = bytearray(0x9000)
    for y in range(block_h):
        for x in range(block_w * 16):
            swizzled = (y // (8 * block_height)) * 512 * block_height * pitch + (x // 64) * 512 * block_height + ((y % (8 * block_height)) // 8) * 512 + ((x % 64) // 32) * 256 + ((y % 8) // 2) * 64 + ((x % 32) // 16) * 32 + (y % 2) * 16 + x % 16
            result[swizzled] = linear[y * block_w * 16 + x]
    return bytes(result)

for target, image in icons.items():
    assert image.size == (144, 144)
    png = root / 'images' / f'{target}.png'
    astc = root / 'images' / f'{target}.astc'
    image.save(png)
    subprocess.run([str(encoder), '-cs', str(png), str(astc), '4x4', '-thorough', '-silent'], check=True)
    encoded = astc.read_bytes()
    assert encoded[:4] == bytes.fromhex('13aba15c')
    assert encoded[4:7] == bytes((4, 4, 1))
    assert len(encoded[16:]) == 36 * 36 * 16
    data = bytearray(template)
    data[0x1000:0xa000] = swizzle_astc(encoded[16:])
    assert len(target) <= 22
    struct.pack_into('<H', data, 0x1b8, len(target))
    data[0x1ba:0x1d0] = target.encode() + bytes(22 - len(target))
    path = mod / f'romfs/UI/Tex/Icon/{target}.bntx.zs'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(zstd.ZstdCompressor(level=19).compress(data))
    # Round-trip the exact packaged texture through the same ASTC decoder used
    # to inspect working native Vow icons.
    decoded = zstd.ZstdDecompressor().decompress(path.read_bytes())
    assert decoded == data
    assert struct.unpack_from('<I', decoded, texture + 0x1c)[0] == 0x2d06
    test = texture2ddecoder.decode_astc(encoded[16:], 144, 144, 4, 4)
    test_image = Image.frombytes('RGBA', (144, 144), test, 'raw', 'BGRA')
    test_image.save(root / 'images' / f'{target}_decoded.png')

# Only icon references change; the emote IDs, names, action parameters, and
# order remain byte-for-byte the D21 baseline after these reference substitutions.
config_path = mod / 'romfs/EmoteConfig/emotes.json'
old_config = config_path.read_text()
config = json.loads(old_config)
references = {
    'tulin': 'SageTulin', 'yunobo': 'SageYunobo', 'mineru': 'SageMineru',
    'sidon': 'SageSidon', 'riju': 'SageRiju', 'warp': 'SageSleep',
}
for key, new_name in references.items():
    config['emotes'][key]['Bntx'] = new_name
for key in config['emotes']:
    for field in config['emotes'][key]:
        if field != 'Bntx':
            assert config['emotes'][key][field] == json.loads(old_config)['emotes'][key][field]
config_path.write_text(json.dumps(config, indent=2) + '\n')

assert (mod / 'exefs/subsdk4').read_bytes() == (baseline / 'exefs/subsdk4').read_bytes()
assert (mod / 'exefs/main.npdm').read_bytes() == (baseline / 'exefs/main.npdm').read_bytes()
assert (mod / 'romfs/EmoteConfig/wheel.json').read_bytes() == (baseline / 'romfs/EmoteConfig/wheel.json').read_bytes()
assert not (mod / 'romfs/UI/LayoutArchive').exists()
assert not (mod / 'romfs/System').exists()

output.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as packed:
    for path in sorted(mod.rglob('*')):
        if path.is_file():
            packed.write(path, str(path.relative_to(mod.parent)))
with zipfile.ZipFile(output) as packed:
    assert packed.testzip() is None
    assert len(packed.namelist()) == 12

report = {
    'zip_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
    'source': 'D21 gameplay baseline',
    'icon_textures': sorted(icons),
    'sage_art_scale': 1.125,
    'horse_tint': '#CAB52D',
    'memory_tint': '#FFFCC6',
    'sleep_core': 'native circular medallion, enlarged; exterior diamond removed',
    'ability_wheel_layout_modified': False,
    'executable_unchanged': True,
}
(root / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(output, output.stat().st_size, report['zip_sha256'])
