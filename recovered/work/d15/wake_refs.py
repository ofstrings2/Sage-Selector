exec(open('work/decode_donors.py').read().split('D=Path')[0])
b=Path('work/decoded/vanilla.0.bin').read_bytes();md=capstone.Cs(capstone.CS_ARCH_ARM64,capstone.CS_MODE_ARM)
for off in range(0,len(b),4):
 w=struct.unpack_from('<I',b,off)[0]
 if w&0x7c000000!=0x14000000:continue
 d=(w&0x3ffffff);d=d-(1<<26) if d&(1<<25) else d
 if off+d*4!=0xaedc50:continue
 ins=list(md.disasm(b[max(0,off-24):off+4],max(0,off-24)))
 if any('#0x7ff' in i.op_str for i in ins): print('\n'.join(f'{i.address:x} {i.mnemonic} {i.op_str}' for i in ins))
