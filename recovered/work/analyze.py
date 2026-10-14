exec(open('work/decode_donors.py').read().split('D=Path')[0])
D=Path('work/decoded');b=(D/'emote.bin').read_bytes();md=capstone.Cs(capstone.CS_ARCH_ARM64,capstone.CS_MODE_ARM);md.skipdata=True
(D/'emote.asm').write_text('\n'.join(f'{x.address:08x} {x.mnemonic:8} {x.op_str}' for x in md.disasm(b[:113264],0)))
a=(D/'vanilla.bin').read_bytes();c=(D/'mineru.bin').read_bytes();ranges=[]
for i in range(0,len(a),4):
 if a[i:i+4]!=c[i:i+4]:
  if ranges and ranges[-1][1]==i:ranges[-1][1]=i+4
  else:ranges.append([i,i+4])
print('main changed ranges',[(hex(x),hex(y)) for x,y in ranges]);(D/'mineru.diff.json').write_text(json.dumps(ranges))
for f in ['Main','Pouch','Event']:
 a=json.loads((D/f'vanilla.{f}.json').read_text());c=json.loads((D/f'mineru.{f}.json').read_text());print(f,len(a['Nodes']),len(c['Nodes']))
 for i,n in enumerate(c['Nodes']):
  if i>=len(a['Nodes']) or n!=a['Nodes'][i]:print(i,n['Name'],json.dumps(n) if f=='Main' and i>=39 else '')
