exec(open('work/decode_donors.py').read().split('D=Path')[0])
import copy,uuid,zstandard as z
D=Path('work/decoded');out=Path('work/build/Sage Wheel v0.1 D02');(out/'exefs').mkdir(parents=True,exist_ok=True);(out/'romfs/Sequence').mkdir(parents=True,exist_ok=True)
syms=json.loads(Path('work/core.symbols.json').read_text());raw=bytearray((D/'emote.bin').read_bytes());source=Path('work/donors/EmoteWheel/exefs/subsdk4').read_bytes()
def branch(at,to):struct.pack_into('<I',raw,at,0x14000000|(((to-at)//4)&0x3ffffff))
for a,b in [(0x7770,0x7910),(0x7c10,0x8050),(0x8180,0x8440),(0x8ea0,0x9570),(0x9b80,0xcf80)]:raw[a:b]=bytes(b-a)
raw[0xa000:0xa000+len(Path('work/core.bin').read_bytes())]=Path('work/core.bin').read_bytes()
raw[0x7800:0x7800+len(Path('work/factory.bin').read_bytes())]=Path('work/factory.bin').read_bytes()
# original close's first instruction reproduced in a small callable trampoline
raw[0x7770:0x7774]=source[0:0] or (D/'emote.bin').read_bytes()[0x85d0:0x85d4];branch(0x7774,0x85d4)
branch(0x85d0,syms['close_wheel']);branch(0xc9e0,syms['init'])
# Physical HID Down bit 15 becomes Minus bit 11 only in retained wheel lifecycle.
patches=[]
for a in [0x885c,0x8a08,0x8b00,0x8e10]:
 w=struct.unpack_from('<I',raw,a)[0]
 if a==0x885c:
  assert w==0xf271029f,hex(w)
  # tst x20,#0x8000 -> tst x20,#0x800
  w=(w&~(0x3f<<16))|(53<<16)
 else:
  # ubfx w4,w7,#15,#1 -> #11,#1
  assert (w>>16)&63==15 and (w>>10)&63==15,hex(w)
  w=(w&~((63<<16)|(63<<10)))|(11<<16)|(11<<10)
 struct.pack_into('<I',raw,a,w);patches.append(hex(a))
# Drop default emote JSON and unused emote-specific strings. Native UI diagnostics retained.
for a,b in [(0x1ceb0,0x1cec8),(0x1ced8,0x1cee8),(0x1d128,0x1d1e8),(0x1d310,0x1dd30)]:raw[a:b]=bytes(b-a)
raw=raw.replace(b'TotK Emotes',b'Sage Wheel ')
# Rebuild NSO with original segment memory addresses and hashes, no full main.
header=bytearray(source[:0x100]);body=bytearray();segments=json.loads((D/'emote.json').read_text())['segments']
for i,(va,size) in enumerate(segments):
 payload=bytes(raw[va:va+size]);comp=lz4.block.compress(payload,store_size=False,mode='high_compression',compression=12)
 struct.pack_into('<I',header,0x10+i*16,0x100+len(body));struct.pack_into('<I',header,0x60+i*4,len(comp));header[0xa0+i*32:0xc0+i*32]=hashlib.sha256(payload).digest();body.extend(comp)
header[0x40:0x60]=hashlib.sha256(bytes(raw)).digest()
(out/'exefs/subsdk4').write_bytes(header+body);(out/'exefs/main.npdm').write_bytes(Path('work/donors/EmoteWheel/exefs/main.npdm').read_bytes());Path('work/sage.memory.bin').write_bytes(raw)
# Minimal Main AINB: preserve every original edge except Minus physical guard.
v=json.loads((D/'vanilla.Main.json').read_text());m=json.loads((D/'mineru.Main.json').read_text());nodes=v['Nodes']
# guard 39, getmask40, maskchecker41, begin42, return43
mapping={47:39,48:40,49:41,8:42,50:8}
for old in [47,48,49]:
 n=copy.deepcopy(m['Nodes'][old]);n['Node Index']=mapping[old];n['GUID']=str(uuid.uuid5(uuid.NAMESPACE_URL,'sage-wheel/'+str(old)))
 n['Queries']=[mapping.get(x,x) for x in n['Queries']]
 for ps in n['Parameters']['Inputs'].values():
  for p in ps:p['Node Index']=mapping.get(p['Node Index'],p['Node Index'])
 for plugs in n['Plugs'].values():
  for p in plugs:p['Node Index']=mapping.get(p['Node Index'],p['Node Index'])
 nodes.append(n)
n=copy.deepcopy(nodes[8]);n['Node Index']=42;n['Name']='SeqOneShotSageWheelBegin';n['GUID']=str(uuid.uuid5(uuid.NAMESPACE_URL,'sage-wheel/begin'));n['Plugs']={'Transition':[{'Node Index':38,'Transition Type':1,'Update Post Calc':True}]};nodes.append(n)
next(p for p in nodes[38]['Plugs']['Child'] if p['Name']=='MinusMenu')['Node Index']=39
blob=ainb.AINB.from_dict(v).to_binary();assert ainb.AINB.from_binary(blob).as_dict()==v
(out/'romfs/Sequence/Main.module.ainb').write_bytes(blob);Path('work/sage.Main.json').write_text(json.dumps(v,indent=2));print('build',len(header+body),'AINB',len(blob),'patches',patches)
