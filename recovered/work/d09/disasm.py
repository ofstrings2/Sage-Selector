exec(open('work/decode_donors.py').read().split('D=Path')[0])
b=Path('work/decoded/vanilla.bin').read_bytes();md=capstone.Cs(capstone.CS_ARCH_ARM64,capstone.CS_MODE_ARM)
for a,n in [(0x219b020,0x2350),(0x219d364,0x1600),(0x1d8fdc0,0x450)]:
 p=Path('work/d09/native_%x.asm'%a);p.write_text('\n'.join(f'{x.address:08x} {x.mnemonic:8} {x.op_str}' for x in md.disasm(b[a:a+n],a)))
