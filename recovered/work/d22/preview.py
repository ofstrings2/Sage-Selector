import importlib.util
import math
import struct
import sys
from pathlib import Path

sys.path.insert(0, 'vendor-python')
from PIL import Image, ImageDraw, ImageFont
import zstandard as zstd

spec = importlib.util.spec_from_file_location('analyze_icons', 'work/d22/analyze_icons.py')
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)

root = Path('work/d22')
mod = root / 'build/Sage Selector'
icons = {name: image.copy() for name, image, _, _ in analysis.items}
for label, asset, tint in [('Horse', 'SageHorse', '#CAB52D'), ('Memory', 'SageMemory', '#FFFCC6')]:
    binary = zstd.ZstdDecompressor().decompress((mod / f'romfs/UI/Tex/Icon/{asset}.bntx.zs').read_bytes())
    texture = struct.unpack_from('<Q', binary, struct.unpack_from('<Q', binary, 0x28)[0])[0]
    image, _ = analysis.image_from_bntx(binary, texture)
    colored = Image.new('RGBA', image.size, tint)
    colored.putalpha(image.getchannel('A'))
    icons[label] = colored

scales = {'Tulin': 1.0, 'Memory': 1.30, 'Yunobo': 1.0, 'Mineru': 1.0,
          'Sidon': 1.0, 'Horse': 0.92, 'Riju': 1.0, 'Sleep': 1.05}
names = ['Tulin', 'Memory', 'Yunobo', 'Mineru', 'Sidon', 'Horse', 'Riju', 'Sleep']
canvas = Image.new('RGB', (1080, 1080), '#1d252b')
draw = ImageDraw.Draw(canvas)
center = (540, 540)
for index, name in enumerate(names):
    angle = math.pi / 2 - index * math.pi / 4
    x = center[0] + 340 * math.cos(angle)
    y = center[1] - 340 * math.sin(angle)
    draw.ellipse((x-140, y-140, x+140, y+140), outline='#56626a', width=2)
    image = icons[name]
    side = round(144 * scales[name])
    image = image.resize((side, side), Image.Resampling.LANCZOS)
    canvas.paste(image, (round(x-side/2), round(y-side/2)), image)
    draw.text((x-25, y+100), name, fill='white')
canvas.save(root / 'wheel_preview.png')
