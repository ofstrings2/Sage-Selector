exec(open('work/decode_donors.py').read().split('D=Path')[0])
s=Path('work/d10/code_refs.py').read_text().replace('targets={0x3710c40,0x375cf86,0x36e0b5c}','targets={0x3733293,0x3701200}')
exec(s)
