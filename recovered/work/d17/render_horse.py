import sys,struct,json
from pathlib import Path
sys.path.insert(0,'work/d11/vendor')
sys.path.insert(0,'inputs/external-reference')
import texture2ddecoder as td
from PIL import Image,ImageDraw
b=Path('work/d11/common.bntx').read_bytes();idx=dict(json.loads(Path('work/d11/texture_index.json').read_text()))
def render(b,p):
 fmt=struct.unpack_from('<I',b,p+0x1c)[0];w,h=struct.unpack_from('<II',b,p+0x24);bh=1<<(struct.unpack_from('<I',b,p+0x34)[0]&7);size=struct.unpack_from('<I',b,p+0x50)[0];table=struct.unpack_from('<Q',b,p+0x70)[0];data=struct.unpack_from('<Q',b,table)[0]
 if fmt==0x1d01:bw=hh=4;bs=8
 elif fmt in (0x2d01,0x2d06):bw=hh=4;bs=16
 else:raise Exception(hex(fmt))
 ww=(w+bw-1)//bw;ht=(h+hh-1)//hh;pitch=(ww*bs+63)//64;raw=bytearray(ww*ht*bs)
 for y in range(ht):
  for x in range(ww*bs):
   at=(y//(8*bh))*512*bh*pitch+(x//64)*512*bh+((y%(8*bh))//8)*512+((x%64)//32)*256+((y%8)//2)*64+((x%32)//16)*32+(y%2)*16+x%16
   raw[y*ww*bs+x]=b[data+at]
 pixels=td.decode_bc4(bytes(raw),w,h) if fmt==0x1d01 else td.decode_astc(bytes(raw),w,h,bw,hh)
 im=Image.frombytes('RGBA',(w,h),pixels,'raw','BGRA')
 if fmt==0x1d01:
  alpha=im.getchannel('R');im=Image.new('RGBA',(w,h),'white');im.putalpha(alpha)
 return im
names=['Nt_HorseIcon_00^d','Nt_Circle64Horse_00^s','MapIconShopHorse_58x58^w','NumDisplay_82x82_Obj_StableHostlePointCard^w']
canvas=Image.new('RGB',(800,240),'#343434');d=ImageDraw.Draw(canvas)
for j,n in enumerate(names):
 print(n,hex(struct.unpack_from('<I',b,idx[n]+0x1c)[0]))
 try:im=render(b,idx[n])
 except Exception as e:print(e);continue
 im.thumbnail((170,170));canvas.paste(im,(j*200+15,20),im);d.text((j*200+5,200),n[:24],fill='white')
canvas.save('work/d17/horse_candidates.png')
