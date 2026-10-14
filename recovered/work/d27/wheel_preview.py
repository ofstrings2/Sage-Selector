"""Static comparison preview for the D27 icon texture sizes."""

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


root = Path('work/d27')
scale = 2
width, height = 1200, 1250
canvas = Image.new('RGB', (width * scale, height * scale), '#304047')
draw = ImageDraw.Draw(canvas)


def point(center, radius, degrees):
    angle = math.radians(degrees)
    return (
        round((center[0] + radius * math.cos(angle)) * scale),
        round((center[1] + radius * math.sin(angle)) * scale),
    )


center = (600, 555)
outer, inner, ring = 485, 225, 355
icons = [
    ('SageTulin', -90), ('SageMemory', -45), ('SageYunobo', 0),
    ('SageMineru', 45), ('SageSidon', 90), ('SageHorse', 135),
    ('SageRiju', 180), ('SageSleep', 225),
]

for name, angle in icons:
    start, end = angle - 20.8, angle + 20.8
    outer_points = [point(center, outer, start + i * (end - start) / 32) for i in range(33)]
    inner_points = [point(center, inner, end - i * (end - start) / 32) for i in range(33)]
    shape = outer_points + inner_points
    selected = name == 'SageSleep'
    draw.polygon(shape, fill='#087fc0' if selected else '#1b2024')
    draw.line(shape + [shape[0]], fill='#ffe795' if selected else '#374047', width=(9 if selected else 4) * scale, joint='curve')

for name, angle in icons:
    image = Image.open(root / 'images' / f'{name}_decoded.png').convert('RGBA')
    # Match the existing preview's smaller Horse pane; only artwork changed.
    side = 166 if name == 'SageHorse' else 197
    image = image.resize((side * scale, side * scale), Image.Resampling.LANCZOS)
    x, y = point(center, ring, angle)
    canvas.paste(image, (x - image.width // 2, y - image.height // 2), image)

x, y = point(center, 0, 0)
draw.ellipse((x-18*scale, y-18*scale, x+18*scale, y+18*scale), outline='#f6dd7b', width=7*scale)
font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 52 * scale)
draw.text((width*scale//2, 1100*scale), 'Sleep', font=font, anchor='mm', fill='#ffffff')
canvas.resize((width, height), Image.Resampling.LANCZOS).save(root / 'wheel_mockup.png')
