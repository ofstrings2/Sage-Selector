exec(open('work/decode_donors.py').read().split('D=Path')[0])
b=Path('work/d11/d10.bin').read_bytes();md=capstone.Cs(capstone.CS_ARCH_ARM64,capstone.CS_MODE_ARM)
for a,n in [(0x9760,0x420),(0x1bb00,0x350),(0x7c10,0x80)]:
 Path('work/d11/self_%x.asm'%a).write_text('\n'.join(f'{i.address:08x} {i.mnemonic:8} {i.op_str}' for i in md.disasm(b[a:a+n],a)))
print(b[:16].hex())
