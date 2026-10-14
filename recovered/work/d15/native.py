exec(open('work/decode_donors.py').read().split('D=Path')[0])
b=Path('work/decoded/vanilla.bin').read_bytes();md=capstone.Cs(capstone.CS_ARCH_ARM64,capstone.CS_MODE_ARM)
for a,n in [(0x83ac04,0x1f0),(0xaedc50,0x340),(0x9ee828,0x170),(0x67e8c8,0x350)]:
 print('FUNC',hex(a));print('\n'.join(f'{i.address:08x} {i.mnemonic} {i.op_str}' for i in md.disasm(b[a:a+n],a)))
