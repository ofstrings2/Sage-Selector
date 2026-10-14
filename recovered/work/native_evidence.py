exec(open('work/decode_donors.py').read().split('D=Path')[0])
import mmh3
b=Path('work/decoded/vanilla.bin').read_bytes(); print('sage keys', [hex(x) for x in struct.unpack_from('<5I',b,0x38238d4)])
for s in ['Wind','Fire','Water','Electric','Soul','Rito','Goron','Zora','Gerudo','Zonau','IsSummon','IsGet','IsHave','PlayerStatus','Companion']:
 print(s,hex(mmh3.hash(s,signed=False)))
a=json.loads(Path('work/decoded/vanilla.Main.json').read_text());c=json.loads(Path('work/decoded/mineru.Main.json').read_text()); print('main38',a['Nodes'][38])
for f,i in [('Pouch',3),('Event',39)]:
 for donor in ['vanilla','mineru']:print(donor,f,json.loads(Path(f'work/decoded/{donor}.{f}.json').read_text())['Nodes'][i])
