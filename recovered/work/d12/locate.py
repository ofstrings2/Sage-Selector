exec(open('work/decode_donors.py').read().split('D=Path')[0])
b=Path('work/decoded/vanilla.bin').read_bytes();names=[b'ExecuteEventPlayerWarpSafePos'];targets={b.find(n) for n in names};print(targets)
s=Path('work/d10/code_refs.py').read_text();s=s.replace('targets={0x3710c40,0x375cf86,0x36e0b5c}','targets='+repr(targets));exec(s)
