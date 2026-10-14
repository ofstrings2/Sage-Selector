exec(open('work/decode_donors.py').read().split('D=Path')[0])
b=Path('work/decoded/vanilla.bin').read_bytes();md=capstone.Cs(capstone.CS_ARCH_ARM64,capstone.CS_MODE_ARM)
blocks=[(0xf68af0,0xa0),(0xddbb04,0x70),(0x80e6c4,0x70),(0x92a530,0x24),(0x92a660,0x28)]
for a,n in blocks:
 print('\n',hex(a));print('\n'.join(f'{x.address:08x} {x.mnemonic} {x.op_str}' for x in md.disasm(b[a:a+n],a)))
print('sage table', [hex(x) for x in struct.unpack_from('<5I',b,0x38238d4)])
# Known native Companion system getter call sites.
count=0
for a in range(0,len(Path('work/decoded/vanilla.0.bin').read_bytes()),4):
 w=struct.unpack_from('<I',b,a)[0]
 if w==0x94000000|(((0xf68af0-a)//4)&0x3ffffff):
  ins=list(md.disasm(b[max(0,a-24):a+8],max(0,a-24)))
  if any(x.mnemonic=='mov' and x.op_str=='w1, #0x12' for x in ins):
   print('\nCall',hex(a));print('\n'.join(f'{x.address:08x} {x.mnemonic} {x.op_str}' for x in ins));count+=1
   if count==3:break
