import struct,json
from pathlib import Path
b=Path('work/d15/toggle.o').read_bytes();shoff=struct.unpack_from('<Q',b,40)[0];n=struct.unpack_from('<H',b,60)[0];sti=struct.unpack_from('<H',b,62)[0]
sects=[struct.unpack_from('<IIQQQQIIQQ',b,shoff+i*64) for i in range(n)];ss=sects[sti];names=b[ss[4]:ss[4]+ss[5]]
name=lambda off:names[off:names.index(0,off)].decode()
locations={'.sleep':(0x81d4,0x8280),'.resolve':(0x1ba70,0x1bb00),'.toggle':(0x1e50,0x1f20),'.wake':(0x1f20,0x2000)}
addr={};raw=bytearray(Path('work/d14/d14.bin').read_bytes());ranges=[]
for i,s in enumerate(sects):
 if s[2]&2 and s[5]:
  start,end=locations[name(s[0])];assert start+s[5]<=end,(name(s[0]),s[5]);addr[i]=start;raw[start:start+s[5]]=b[s[4]:s[4]+s[5]];ranges.append([start,start+s[5]]);print(name(s[0]),hex(start),s[5])
symsec=next(s for s in sects if s[1]==2);ss=sects[symsec[6]];strings=b[ss[4]:ss[4]+ss[5]]
syms=[];symbols={'__module_start':0,'hid':0x7910,'ticks':0xd614,'execute':0x7c10,'wheel_tick':0x8810,'close_wheel':0x85d0,'previous_utility':0x1bf08}
for p in range(symsec[4],symsec[4]+symsec[5],24):
 no,info,other,idx,val,size=struct.unpack_from('<IBBHQQ',b,p);nm=strings[no:strings.index(0,no)].decode();syms.append((nm,idx,val))
 if idx in addr:symbols[nm]=addr[idx]+val
for s in sects:
 if s[1]!=4 or s[7] not in addr:continue
 for p in range(s[4],s[4]+s[5],24):
  off,info,add=struct.unpack_from('<QQq',b,p);typ=info&0xffffffff;si=info>>32;nm,idx,val=syms[si];target=(addr[idx]+val if idx in addr else symbols[nm])+add;pc=addr[s[7]]+off
  ins=struct.unpack_from('<I',raw,pc)[0]
  if typ in (282,283):
   d=target-pc;assert d%4==0 and -(1<<27)<=d<(1<<27);ins=(ins&0xfc000000)|((d>>2)&0x3ffffff)
  elif typ==275:
   d=(target>>12)-(pc>>12);ins=(ins&~0x60ffffe0)|((d&3)<<29)|(((d>>2)&0x7ffff)<<5)
  elif typ==277:ins=(ins&~0x3ffc00)|((target&4095)<<10)
  elif typ in (278,284,285,286,299):
   shift={278:0,284:1,285:2,286:3,299:4}[typ];assert not target%(1<<shift);ins=(ins&~0x3ffc00)|(((target&4095)>>shift)<<10)
  else:raise ValueError((typ,nm,hex(pc)))
  struct.pack_into('<I',raw,pc,ins)
Path('work/d15/d15.bin').write_bytes(raw);Path('work/d15/symbols.json').write_text(json.dumps(symbols,indent=2));Path('work/d15/ranges.json').write_text(json.dumps(ranges))
