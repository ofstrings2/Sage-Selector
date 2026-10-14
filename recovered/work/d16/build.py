from pathlib import Path
import struct,json
b=bytearray(Path('work/d15/d15.bin').read_bytes())
a=0x8184
# Live on-foot Whistle entry supersedes an unmatched old mounted node.
# Keep D11 ACTIVE/REQUEST reset and tail-call the original context reacquisition.
page_delta=(0x59000>>12)-(a>>12)
adrp=0x90000008|((page_delta&3)<<29)|(((page_delta>>2)&0x7ffff)<<5)
code=[adrp,0xf900111f,0xb900291f,0xb4000000|(((0x8280-(a+12))//4)<<5),0xf900051f,0x14000000|(((0x8280-(a+20))//4)&0x3ffffff)]
for i,w in enumerate(code):struct.pack_into('<I',b,a+4*i,w)
# Original trailing instructions are now unreachable. Preserve those bytes.
Path('work/d16/d16.bin').write_bytes(b)
Path('work/d16/changes.json').write_text(json.dumps([[a,a+24]]))
s=Path('work/d16/repro_template.c').read_text().replace('work/d15/d15.bin','work/d16/d16.bin').replace('EXPECTED_FIXED','1')
Path('work/d16/repro_d16.c').write_text(s)
