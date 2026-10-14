exec(open('work/decode_donors.py').read().split('D=Path')[0])
b=Path('work/decoded/vanilla.bin').read_bytes();md=capstone.Cs(capstone.CS_ARCH_ARM64,capstone.CS_MODE_ARM)
for a,n in [(0x107e9a0,0xb0),(0x92a8cc,0x280),(0x11dc374,0xb0)]:
 t='\n'.join(f'{x.address:08x} {x.mnemonic:8} {x.op_str}' for x in md.disasm(b[a:a+n],a));Path(f'work/d10/native_{a:x}.asm').write_text(t)
print(Path('work/d10/native_107e9a0.asm').read_text())
for s in [b'RaumiGolem',b'RideRobot']:
 for m in re.finditer(s,b):
  if m.start()>0x2b19a50:
   p=m.start();left=b.rfind(b'\0',max(0,p-120),p)+1;end=b.find(b'\0',p);ss=b[left:end]
   if len(ss)<180 and any(x in ss.lower() for x in [b'ride',b'rid',b'player']):print(hex(left),ss.decode(errors='replace'))
