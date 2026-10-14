import struct,sys
from pathlib import Path
sys.path.insert(0,'work/d11/vendor')
sys.path.insert(0,'inputs/external-reference')
import zstandard as zstd
import texture2ddecoder as decoder
from PIL import Image

root=Path('work/d19')
src=Path('work/d18/build/Sage Selector D18/romfs/UI/Tex/Icon/SageMemory.bntx.zs')
b=zstd.ZstdDecompressor().decompress(src.read_bytes())
tex=struct.unpack_from('<Q',b,struct.unpack_from('<Q',b,0x28)[0])[0]
assert struct.unpack_from('<I',b,tex+0x1c)[0]==0x1d01 # BC4 alpha mask
w,h=struct.unpack_from('<II',b,tex+0x24)
assert (w,h)==(72,72)
bh=1<<(struct.unpack_from('<I',b,tex+0x34)[0]&7)
table=struct.unpack_from('<Q',b,tex+0x70)[0]
data=struct.unpack_from('<Q',b,table)[0]
old_size=struct.unpack_from('<I',b,tex+0x50)[0]
old_rlt=struct.unpack_from('<I',b,0x18)[0]
assert (data,old_size,old_rlt)==(0x1000,0x1800,0x3000)

blocks_w=(w+3)//4;blocks_h=(h+3)//4
def offset(x_byte,y,pitch):
 return ((y//(8*bh))*512*bh*pitch+(x_byte//64)*512*bh+
         ((y%(8*bh))//8)*512+((x_byte%64)//32)*256+
         ((y%8)//2)*64+((x_byte%32)//16)*32+(y%2)*16+x_byte%16)
def linearize(data_bytes,block_bytes):
 pitch=(blocks_w*block_bytes+63)//64
 return bytes(data_bytes[offset(x*block_bytes+j,y,pitch)]
              for y in range(blocks_h) for x in range(blocks_w)
              for j in range(block_bytes))
def swizzle(linear,block_bytes):
 pitch=(blocks_w*block_bytes+63)//64
 groups=(blocks_h+8*bh-1)//(8*bh)
 size=pitch*512*bh*groups
 out=bytearray(size)
 for y in range(blocks_h):
  for x in range(blocks_w):
   q=(y*blocks_w+x)*block_bytes
   for j in range(block_bytes):out[offset(x*block_bytes+j,y,pitch)]=linear[q+j]
 return out

old_linear=linearize(b[data:data+old_size],8)
# A quiet blue-white tint close to the Adventure Log's Memory treatment.
rgb=(218,235,247)
rgb565=((rgb[0]>>3)<<11)|((rgb[1]>>2)<<5)|(rgb[2]>>3)
color=struct.pack('<HHI',rgb565,rgb565,0)
new_linear=b''.join(old_linear[i:i+8]+color for i in range(0,len(old_linear),8))
new_data=swizzle(new_linear,16)
assert len(new_data)==0x2800
assert linearize(new_data,16)==new_linear

# BC3's alpha block is exactly the original BC4 block. Decoding proves every
# icon edge/transparent pixel is preserved while only RGB receives the tint.
old_pixels=decoder.decode_bc4(old_linear,w,h)
new_pixels=decoder.decode_bc3(new_linear,w,h)
old_image=Image.frombytes('RGBA',(w,h),old_pixels,'raw','BGRA')
new_image=Image.frombytes('RGBA',(w,h),new_pixels,'raw','BGRA')
assert list(old_image.getchannel('R').getdata())==list(new_image.getchannel('A').getdata())
new_image.resize((288,288)).save(root/'SageMemory_blue_preview.png')

rlt=(data+len(new_data)+0xfff)&~0xfff
v=bytearray(b[:data]);v.extend(new_data);v.extend(bytes(rlt-len(v)));v.extend(b[old_rlt:])
struct.pack_into('<II',v,0x18,rlt,len(v))
struct.pack_into('<I',v,tex+0x1c,0x1c06) # BC3 sRGB
struct.pack_into('<I',v,tex+0x50,len(new_data))
v[tex+0x54:tex+0x58]=bytes((2,3,4,5)) # RGBA, rather than white + BC4 alpha
struct.pack_into('<I',v,rlt+4,rlt)
struct.pack_into('<Q',v,0xff8,rlt-0xff0)
struct.pack_into('<I',v,rlt+0x34,rlt-0xff0)
assert v[rlt:rlt+4]==b'_RLT' and len(v)==0x4068
(root/'SageMemory_blue.bntx').write_bytes(v)
(root/'SageMemory_blue.bntx.zs').write_bytes(zstd.ZstdCompressor(level=19).compress(v))
print('RGBA tint',rgb,'BC3',hex(rgb565),'alpha pixels identical',w*h,'BNTX',len(v))
