import sys,struct
from pathlib import Path
sys.path.insert(0,'work/d11/vendor')
sys.path.insert(0,'inputs/external-reference')
import zstandard as z
from PIL import Image,ImageDraw
from render_horse import render
files=sorted(Path('work/d17').glob('GameRomHorse*.bntx.zs'))
canvas=Image.new('RGB',(4*240,4*250),'#333333');d=ImageDraw.Draw(canvas)
for i,f in enumerate(files):
 b=z.ZstdDecompressor().decompress(f.read_bytes());p=struct.unpack_from('<Q',b,struct.unpack_from('<Q',b,0x28)[0])[0]
 print(f.name,len(b),hex(struct.unpack_from('<I',b,p+0x1c)[0]),struct.unpack_from('<II',b,p+0x24))
 im=render(b,p);im.thumbnail((190,190));x=(i%4)*240+25;y=(i//4)*250+15;canvas.paste(im,(x,y),im);d.text((x,y+195),f.stem[:24],fill='white')
canvas.save('work/d17/stable_icons.png')
