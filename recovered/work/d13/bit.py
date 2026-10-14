exec(open('work/decode_donors.py').read().split('D=Path')[0])
b=Path('work/decoded/vanilla.bin').read_bytes();md=capstone.Cs(capstone.CS_ARCH_ARM64,capstone.CS_MODE_ARM)
for a,n in [(0xba9e90,0xb0),(0x786948,0xc0)]:
 print('\nFUNC',hex(a));print('\n'.join(f'{i.address:08x} {i.mnemonic} {i.op_str}' for i in md.disasm(b[a:a+n],a)))
