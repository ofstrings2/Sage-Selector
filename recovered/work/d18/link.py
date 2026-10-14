import struct,json
from pathlib import Path

root=Path('work/d18');obj=(root/'autoskip.o').read_bytes()
raw=bytearray(Path('work/d17/d17.bin').read_bytes())
raw[0x3034:0x350c]=bytes(0x350c-0x3034)
shoff=struct.unpack_from('<Q',obj,40)[0]
count=struct.unpack_from('<H',obj,60)[0]
sti=struct.unpack_from('<H',obj,62)[0]
sects=[struct.unpack_from('<IIQQQQIIQQ',obj,shoff+i*64) for i in range(count)]
st=sects[sti];names=obj[st[4]:st[4]+st[5]]
name=lambda off:names[off:names.index(0,off)].decode()
locations={'.autoskip':(0x3034,0x4000)}
addr={};ranges=[[0x3034,0x350c]]
for i,s in enumerate(sects):
 if s[2]&2 and s[5]:
  start,end=locations[name(s[0])]
  assert start+s[5]<=end
  addr[i]=start
  raw[start:start+s[5]]=obj[s[4]:s[4]+s[5]]
  ranges.append([start,start+s[5]])
symsec=next(s for s in sects if s[1]==2)
strings_sec=sects[symsec[6]]
strings=obj[strings_sec[4]:strings_sec[4]+strings_sec[5]]
syms=[];symbols={'__module_start':0}
for p in range(symsec[4],symsec[4]+symsec[5],24):
 no,info,other,idx,val,size=struct.unpack_from('<IBBHQQ',obj,p)
 nm=strings[no:strings.index(0,no)].decode();syms.append((nm,idx,val))
 if idx in addr:symbols[nm]=addr[idx]+val
for s in sects:
 if s[1]!=4 or s[7] not in addr:continue
 for p in range(s[4],s[4]+s[5],24):
  off,info,add=struct.unpack_from('<QQq',obj,p)
  typ=info&0xffffffff;si=info>>32;nm,idx,val=syms[si]
  target=(addr[idx]+val if idx in addr else symbols[nm])+add
  pc=addr[s[7]]+off
  ins=struct.unpack_from('<I',raw,pc)[0]
  if typ in (282,283):
   d=target-pc;assert d%4==0 and -(1<<27)<=d<(1<<27)
   ins=(ins&0xfc000000)|((d>>2)&0x3ffffff)
  elif typ==275:
   d=(target>>12)-(pc>>12)
   ins=(ins&~0x60ffffe0)|((d&3)<<29)|(((d>>2)&0x7ffff)<<5)
  elif typ==277:
   ins=(ins&~0x3ffc00)|((target&4095)<<10)
  else:raise ValueError((typ,nm,hex(pc)))
  struct.pack_into('<I',raw,pc,ins)

def patch(a,w):
 struct.pack_into('<I',raw,a,w);ranges.append([a,a+4])
def branch(a,b):return 0x94000000|(((b-a)//4)&0x3ffffff)
# The event request and all other D17 code remain unchanged. Repoint only
# its existing wrapper call to the corrected input adapter.
patch(0x9074,branch(0x9074,symbols['memory_request_wrapper']))
assert 0x1dfa0+struct.unpack_from('<I',raw,0x1dfac)[0]==0x59090
(root/'d18.bin').write_bytes(raw)
(root/'symbols.json').write_text(json.dumps(symbols,indent=2))
(root/'changes.json').write_text(json.dumps(ranges,indent=2))
print('autoskip code',hex(0x3034),hex(0x3034+sects[next(i for i,s in enumerate(sects) if name(s[0])=='.autoskip')][5]),'wrapper',hex(symbols['memory_request_wrapper']))
