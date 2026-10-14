import json,struct
from pathlib import Path

w=Path('work/d19')
b=bytearray(Path('work/d18/d18.bin').read_bytes())
def imm(a,old,new):
 word=struct.unpack_from('<I',b,a)[0]
 assert ((word>>5)&0xffff)==old,(hex(a),hex(word))
 struct.pack_into('<I',b,a,(word&~0x1fffe0)|(new<<5))

# Initial Memory-event wait: 4 x 19,200,000 ticks -> 3 x 19,200,000 ticks.
# The retry cadence and all other D18 instructions remain byte-identical.
imm(0x3224,0xe000,0xe800)
imm(0x3228,0x0493,0x036e)
assert ((struct.unpack_from('<I',b,0x3224)[0]>>5)&0xffff)|(((struct.unpack_from('<I',b,0x3228)[0]>>5)&0xffff)<<16)==3*19200000
(w/'d19.bin').write_bytes(b)
(w/'changes.json').write_text(json.dumps([[0x3224,0x322c]]))
