exec(open('work/decode_donors.py').read().split('D=Path')[0])
b=Path('work/decoded/emote.bin').read_bytes();md=capstone.Cs(capstone.CS_ARCH_ARM64,capstone.CS_MODE_ARM);md.skipdata=True;md.detail=True;regs={};out=[]
for x in md.disasm(b[:113264],0):
 comment=''
 if x.mnemonic=='adrp':regs[x.operands[0].reg]=x.operands[1].imm
 elif x.mnemonic=='add' and len(x.operands)==3 and x.operands[2].type==2 and x.operands[1].reg in regs:
  p=regs[x.operands[1].reg]+x.operands[2].imm
  if 0x1c000<=p<0x1de00:
   t=b[p:b.find(b'\0',p)].decode(errors='replace');comment=' // '+t
 if x.mnemonic in ['ret','b']:regs={}
 out.append(f'{x.address:08x} {x.mnemonic:8} {x.op_str}{comment}')
Path('work/decoded/emote.annotated.asm').write_text('\n'.join(out))
