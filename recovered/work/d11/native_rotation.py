exec(open('work/decode_donors.py').read().split('D=Path')[0])
b=Path('work/decoded/vanilla.bin').read_bytes();md=capstone.Cs(capstone.CS_ARCH_ARM64,capstone.CS_MODE_ARM)
for a,n in [(0x1b1e4f8,0x3c),(0xbf82b4,0x160)]:
 print('\n'.join(f'{i.address:08x} {i.mnemonic:8} {i.op_str}' for i in md.disasm(b[a:a+n],a)))
