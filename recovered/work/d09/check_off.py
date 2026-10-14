exec(open('work/decode_donors.py').read().split('D=Path')[0])
b=Path('work/decoded/mineru.bin').read_bytes();a=45193808;md=capstone.Cs(capstone.CS_ARCH_ARM64,capstone.CS_MODE_ARM)
print('\n'.join(f'{x.address:x} {x.mnemonic} {x.op_str}' for x in md.disasm(b[a:a+592],a)))
