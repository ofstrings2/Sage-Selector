exec(open('work/decode_donors.py').read().split('D=Path')[0])
r=json.load(open('work/d10/relocs.json'));b=Path('work/decoded/vanilla.bin').read_bytes();md=capstone.Cs(capstone.CS_ARCH_ARM64,capstone.CS_MODE_ARM)
for at in range(0x446bb60,0x446bc70,8):
 v=r.get(str(at),0);print(hex(at),hex(v))
 if at>=0x446bc20 and 0<v<0x2b17000:print('\n'.join(f'{i.address:08x} {i.mnemonic} {i.op_str}' for i in md.disasm(b[v:v+0x90],v)))
