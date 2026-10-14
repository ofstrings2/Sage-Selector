import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, 'work/d11/vendor')
sys.path.insert(0, 'vendor-python')
import texture2ddecoder as decoder
from PIL import Image, ImageDraw
exec(open('work/resources.py').read().split("f='UI/")[0])

destination = Path('work/d22')
combined = Path('work/d11/common.bntx').read_bytes()
index = dict(json.loads(Path('work/d11/texture_index.json').read_text()))

def image_from_bntx(raw, texture):
    format_ = struct.unpack_from('<I', raw, texture + 0x1c)[0]
    width, height = struct.unpack_from('<II', raw, texture + 0x24)
    block_height = 1 << (struct.unpack_from('<I', raw, texture + 0x34)[0] & 7)
    table = struct.unpack_from('<Q', raw, texture + 0x70)[0]
    data = struct.unpack_from('<Q', raw, table)[0]
    block_bytes = 8 if format_ == 0x1d01 else 16
    assert format_ in (0x1d01, 0x2d06)
    blocks_width, blocks_height = (width + 3) // 4, (height + 3) // 4
    pitch = (blocks_width * block_bytes + 63) // 64
    linear = bytearray(blocks_width * blocks_height * block_bytes)
    for y in range(blocks_height):
        for x in range(blocks_width * block_bytes):
            offset = (y // (8 * block_height)) * 512 * block_height * pitch + (x // 64) * 512 * block_height + ((y % (8 * block_height)) // 8) * 512 + ((x % 64) // 32) * 256 + ((y % 8) // 2) * 64 + ((x % 32) // 16) * 32 + (y % 2) * 16 + x % 16
            linear[y * blocks_width * block_bytes + x] = raw[data + offset]
    pixels = decoder.decode_bc4(bytes(linear), width, height) if format_ == 0x1d01 else decoder.decode_astc(bytes(linear), width, height, 4, 4)
    image = Image.frombytes('RGBA', (width, height), pixels, 'raw', 'BGRA')
    if format_ == 0x1d01:
        alpha = image.getchannel('R')
        image = Image.new('RGBA', (width, height), 'white')
        image.putalpha(alpha)
    return image, format_

def game_icon(name):
    raw = dec(R / f'UI/Tex/Icon/{name}.bntx.zs')
    pointer = struct.unpack_from('<Q', raw, struct.unpack_from('<Q', raw, 0x28)[0])[0]
    return image_from_bntx(raw, pointer)

def common_icon(name):
    return image_from_bntx(combined, index[name])

items = [
    ('Tulin', *game_icon('Obj_SageSoul_Rito'), None),
    ('Memory', *common_icon('MapIconDragonTears_00^s'), '#FFFCC6'),
    ('Yunobo', *game_icon('Obj_SageSoul_Goron'), None),
    ('Mineru', *game_icon('Obj_SageSoul_Zonau'), None),
    ('Sidon', *game_icon('Obj_SageSoul_Zora'), None),
    ('Horse', *common_icon('HakushaFlat_00^s'), '#CAB52D'),
    ('Riju', *game_icon('Obj_SageSoul_Gerudo'), None),
    ('Sleep', *game_icon('Obj_WarpDLC_Prototype'), None),
]

sheet = Image.new('RGB', (4 * 250, 2 * 285), '#22272c')
draw = ImageDraw.Draw(sheet)
metrics = {}
for number, (name, image, format_, tint) in enumerate(items):
    alpha = image.getchannel('A')
    if tint:
        colored = Image.new('RGBA', image.size, tint)
        colored.putalpha(alpha)
        image = colored
    mask = alpha.point(lambda a: 255 if a >= 32 else 0)
    bounds = mask.getbbox()
    assert bounds
    diameter = max(bounds[2] - bounds[0], bounds[3] - bounds[1])
    center = ((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2)
    metrics[name] = {'format': hex(format_), 'texture': list(image.size), 'alpha_bbox_32': list(bounds), 'bbox_diameter': diameter, 'bbox_fraction': round(diameter / max(image.size), 4), 'bbox_center': center, 'native_tint': tint}
    column, row = number % 4, number // 4
    x0, y0 = column * 250 + 40, row * 285 + 25
    scaled = image.resize((180, 180), Image.Resampling.LANCZOS)
    sheet.paste(scaled, (x0, y0), scaled)
    draw.ellipse((x0, y0, x0 + 180, y0 + 180), outline='#637077', width=1)
    draw.text((x0, y0 + 192), f'{name} {image.width}x{image.height} core {diameter}px', fill='#efefef')
    image.save(destination / f'{name}.png')
sheet.save(destination / 'native_icon_sheet.png')
(destination / 'icon_metrics.json').write_text(json.dumps(metrics, indent=2) + '\n')
print(json.dumps(metrics, indent=2))
