exec(open('work/decode_donors.py').read().split('D=Path')[0])
b=Path('work/decoded/vanilla.bin').read_bytes();need=[b'UI/AdventureMemorySetTable/',b'OneShotUpdateAdventureMemoryGameData',b'ExecuteWaitFinishAdventureMemoryDirection'];targets=set()
for s in need:
 p=b.find(s);print(s,hex(p));targets.add(p)
s=Path('work/d10/code_refs.py').read_text();s=s.replace('targets={0x3710c40,0x375cf86,0x36e0b5c}','targets='+repr(targets));exec(s)
