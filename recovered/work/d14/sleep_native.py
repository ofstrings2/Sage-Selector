exec(open('work/decode_donors.py').read().split('D=Path')[0])
b=Path('work/decoded/vanilla.bin').read_bytes();md=capstone.Cs(capstone.CS_ARCH_ARM64,capstone.CS_MODE_ARM)
for a,n in [(0xfa7f08,0x40),(0x83ac04,0x150),(0x1254254,0x130),(0x15d32d0,0x100),(0x9ee828,0x60),(0x67e8c8,0x60)]:
 print('FUNC',hex(a));print('\n'.join(f'{i.address:08x} {i.mnemonic} {i.op_str}' for i in md.disasm(b[a:a+n],a)))
for a in [0x37d35d9,0x37be691]:print(hex(a),b[a:b.find(b'\0',a)])
