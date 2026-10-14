exec(open('work/decode_donors.py').read().split('D=Path')[0])
b=Path('work/decoded/vanilla.bin').read_bytes();words=struct.unpack('<%dI'%(len(Path('work/decoded/vanilla.0.bin').read_bytes())//4),Path('work/decoded/vanilla.0.bin').read_bytes());targets={0x3710c40,0x375cf86,0x36e0b5c};md=capstone.Cs(capstone.CS_ARCH_ARM64,capstone.CS_MODE_ARM)
for i,w in enumerate(words):
 if w&0x9f000000!=0x90000000:continue
 imm=((w>>5&0x7ffff)<<2)|(w>>29&3);imm=imm-(1<<21) if imm&(1<<20) else imm;page=((i*4)&~4095)+(imm<<12)
 if page not in {t&~4095 for t in targets}:continue
 reg=w&31
 for j in range(i+1,min(i+24,len(words))):
  v=words[j]
  if v&0xffc00000==0x91000000 and v>>5&31==reg and page+(v>>10&4095) in targets:
   print('STRING',hex(page+(v>>10&4095)),'at',hex(i*4),hex(j*4));print('\n'.join(f'{x.address:x} {x.mnemonic} {x.op_str}' for x in md.disasm(b[max(0,i*4-16):j*4+32],max(0,i*4-16))))
