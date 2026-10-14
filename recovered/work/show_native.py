exec(open('work/decode_donors.py').read().split('D=Path')[0])
b=Path('work/decoded/vanilla.bin').read_bytes();md=capstone.Cs(capstone.CS_ARCH_ARM64,capstone.CS_MODE_ARM)
for a,n in [(0x196110c,0x230),(0x92a8cc,0x200)]:
 print('\nFUNCTION',hex(a));print('\n'.join(f'{x.address:08x} {x.mnemonic:8} {x.op_str}' for x in md.disasm(b[a:a+n],a)))
