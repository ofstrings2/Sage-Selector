exec(open('work/decode_donors.py').read().split('D=Path')[0])
b=Path('work/decoded/vanilla.bin').read_bytes();md=capstone.Cs(capstone.CS_ARCH_ARM64,capstone.CS_MODE_ARM)
for a,n in [(0x1d8fee0,0x700)]:Path('work/d11/native_%x.asm'%a).write_text('\n'.join(f'{i.address:08x} {i.mnemonic:8} {i.op_str}' for i in md.disasm(b[a:a+n],a)))
for s in [b'Whistle',b'AdventureMemory',b'DmT_OP_GanonWakeUp_PreRender_Memory',b'EventRequest',b'PlayerWarp',b'ReturnToSafePos']:
 hits=[];i=0
 while True:
  i=b.find(s,i)
  if i<0:break
  hits.append([hex(i),b[max(0,i-30):b.find(b'\0',i)].decode(errors='replace')]);i+=len(s)
 print(s,hits[:40])
