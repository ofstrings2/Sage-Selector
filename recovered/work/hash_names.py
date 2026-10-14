exec(open('work/decode_donors.py').read().split('D=Path')[0])
import mmh3,zlib
b=Path('work/decoded/vanilla.1.bin').read_bytes(); wanted={0x691f2be1,0xc5a49707,0x28cab8be}
for m in re.finditer(rb'[A-Za-z_][A-Za-z_0-9:./]{2,100}\x00',b):
 s=m.group()[:-1]
 if mmh3.hash(s,signed=False) in wanted or zlib.crc32(s) in wanted:print(hex(mmh3.hash(s,signed=False)),hex(zlib.crc32(s)),s)
