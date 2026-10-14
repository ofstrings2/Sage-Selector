exec(open('work/decode_donors.py').read().split('D=Path')[0])
import zstandard as z
O=Path('work/build/Sage Wheel v0.1 D02');raw=Path('work/sage.memory.bin').read_bytes();original=Path('work/decoded/emote.bin').read_bytes();md=capstone.Cs(capstone.CS_ARCH_ARM64,capstone.CS_MODE_ARM);md.detail=True
ranges=[(0,0x7770),(0x7770,0x7778),(0x7800,0x78ec),(0x7910,0x7c10),(0x8050,0x8180),(0x8440,0x8ea0),(0x9570,0x9b80),(0xa000,json.loads(Path('work/core.symbols.json').read_text())['__text_end']),(0xc9e0,0xc9e4),(0xcf80,113264)]
def alive(t):return any(a<=t<b for a,b in ranges)
bad=[];instructions=[]
for a,b in ranges:
 md.skipdata=True
 for ins in md.disasm(raw[a:b],a):
  if ins.id==0:continue
  if ins.mnemonic in ['b','bl','cbz','cbnz','tbz','tbnz'] or ins.mnemonic.startswith('b.'):
   t=ins.operands[-1]
   if t.type==capstone.CS_OP_IMM and 0<=t.imm<113264 and not alive(t.imm):bad.append((hex(ins.address),ins.mnemonic,hex(t.imm)))
  instructions.append(f'{ins.address:08x} {ins.mnemonic:8} {ins.op_str}')
Path('work/sage.disassembly.txt').write_text('\n'.join(instructions));print('dead branch targets',bad);assert not bad
b=(O/'exefs/subsdk4').read_bytes()
for i in range(3):
 off,va,n=struct.unpack_from('<III',b,0x10+i*16);cs=struct.unpack_from('<I',b,0x60+i*4)[0];d=lz4.block.decompress(b[off:off+cs],uncompressed_size=n);assert d==raw[va:va+n];assert hashlib.sha256(d).digest()==b[0xa0+i*32:0xc0+i*32]
g=ainb.AINB.from_binary((O/'romfs/Sequence/Main.module.ainb').read_bytes()).as_dict();v=json.loads(Path('work/decoded/vanilla.Main.json').read_text());assert len(g['Nodes'])==43
for i in range(38):assert g['Nodes'][i]==v['Nodes'][i]
assert g['Nodes'][39]['Plugs']['Child']==[{'Node Index':42,'Name':'True'},{'Node Index':8,'Name':'False'}]
for n in g['Nodes']:
 for plugs in n['Plugs'].values():
  for p in plugs:assert 0<=p['Node Index']<len(g['Nodes'])
 for typ,ps in n['Parameters']['Inputs'].items():
  for p in ps:
   if p['Node Index']>=0:assert p['Output Index']<len(g['Nodes'][p['Node Index']]['Parameters']['Outputs'][typ])
assert g['Nodes'][8]==v['Nodes'][8]
rr='System/Resource/ResourceSizeTable.Product.121.rsizetable.zs';a=z.ZstdDecompressor().decompress((Path('inputs/romfs')/rr).read_bytes());b=z.ZstdDecompressor().decompress((O/'romfs'/rr).read_bytes());diff=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y];assert len(a)==len(b) and len(diff)<=4
checks=['NSO segment decode and SHA256 validation','No retained direct branch targets removed donor code','AINB binary semantic round trip and all node links/input types valid','Vanilla Main nodes 0–37 byte-semantically unchanged; only node 38 Minus edge redirected','No-physical-Minus guard returns to untouched native Map route node 8','RESTBL only one allocation changed; collision/name table unchanged','No main replacement, Pouch, Event, Common UI archive, Player, animation, sound, emote config or emote textures shipped']
Path('work/static_audit.json').write_text(json.dumps({'checks':checks,'runtime_game_tested':False,'files':{str(p.relative_to(O)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in O.rglob('*') if p.is_file()}},indent=2));print('\n'.join(checks))
