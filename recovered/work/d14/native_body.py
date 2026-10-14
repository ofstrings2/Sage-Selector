exec(open('work/decode_donors.py').read().split('D=Path')[0])
r=json.load(open('work/d10/relocs.json'));b=Path('work/decoded/vanilla.bin').read_bytes();md=capstone.Cs(capstone.CS_ARCH_ARM64,capstone.CS_MODE_ARM)
for name in [0x293fb38,0x293ed78]:
 a=next(int(k)-0x88 for k,v in r.items() if v==name);print('CLASS',hex(a))
 for off in [0x110]:
  v=r[str(a+off)];print('METHOD',hex(off),hex(v));print('\n'.join(f'{i.address:08x} {i.mnemonic} {i.op_str}' for i in md.disasm(b[v:v+0x170],v)))
