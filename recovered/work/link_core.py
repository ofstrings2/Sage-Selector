import struct,json
from pathlib import Path
b=Path('work/core.o').read_bytes();shoff=struct.unpack_from('<Q',b,40)[0];n=struct.unpack_from('<H',b,60)[0];sti=struct.unpack_from('<H',b,62)[0]
sects=[struct.unpack_from('<IIQQQQIIQQ',b,shoff+i*64) for i in range(n)];strsec=sects[sti];names=b[strsec[4]:strsec[4]+strsec[5]]
name=lambda off:names[off:names.index(0,off)].decode()
addr={};out=bytearray();base=0xa000
for i,s in enumerate(sects):
 if s[2]&2:
  align=s[8];out.extend(bytes(-(base+len(out))%align));addr[i]=base+len(out);out.extend(b[s[4]:s[4]+s[5]] if s[1]!=8 else bytes(s[5]));print(name(s[0]),hex(addr[i]),s[5])
symsec=next(s for s in sects if s[1]==2);ss=sects[symsec[6]];strings=b[ss[4]:ss[4]+ss[5]]
syms=[];symbols={'__module_start':0,'donor_hook':0x1bd0,'donor_open_step':0x8810,'donor_close_body':0x7770,'donor_cleanup':0x8050,'factory0':0x7800,'factory1':0x7880,'memcpy':0xdd40,'memset':0xd780}
for p in range(symsec[4],symsec[4]+symsec[5],24):
 no,info,other,idx,val,size=struct.unpack_from('<IBBHQQ',b,p);nm=strings[no:strings.index(0,no)].decode();syms.append((nm,idx,val))
 if idx in addr:symbols[nm]=addr[idx]+val
for s in sects:
 if s[1]!=4 or s[7] not in addr:continue
 for p in range(s[4],s[4]+s[5],24):
  off,info,add=struct.unpack_from('<QQq',b,p);typ=info&0xffffffff;si=info>>32;nm,idx,val=syms[si];target=(addr[idx]+val if idx in addr else symbols[nm])+add;pc=addr[s[7]]+off;o=pc-base
  if typ==257:raise ValueError('Absolute pointer requires NSO runtime relocation')
  ins=struct.unpack_from('<I',out,o)[0]
  if typ in (282,283):
   d=target-pc;assert d%4==0 and -(1<<27)<=d<(1<<27);ins=(ins&0xfc000000)|((d>>2)&0x3ffffff)
  elif typ==275:
   d=(target>>12)-(pc>>12);ins=(ins&~0x60ffffe0)|((d&3)<<29)|(((d>>2)&0x7ffff)<<5)
  elif typ==277:ins=(ins&~0x3ffc00)|((target&4095)<<10)
  elif typ in (278,284,285,286,299):
   shift={278:0,284:1,285:2,286:3,299:4}[typ];assert not target% (1<<shift);ins=(ins&~0x3ffc00)|(((target&4095)>>shift)<<10)
  else:raise ValueError((typ,nm,hex(pc)))
  struct.pack_into('<I',out,o,ins)
assert base+len(out)<0xc9e0,hex(base+len(out))
symbols['__text_end']=next(addr[i]+v[5] for i,v in enumerate(sects) if i in addr and name(v[0])=='.text')
Path('work/core.bin').write_bytes(out);Path('work/core.symbols.json').write_text(json.dumps(symbols,indent=2));print('linked',len(out),hex(base+len(out)))
