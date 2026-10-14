exec(open('work/decode_donors.py').read().split('D=Path')[0])
b=bytearray(Path('work/d11/horse_linked.bin').read_bytes());ranges=json.load(open('work/d11/horse_ranges.json'))
def patch(a,words):b[a:a+4*len(words)]=struct.pack('<'+'I'*len(words),*words);ranges.append([a,a+4*len(words)])
def br(a,t,link=False):return (0x94000000 if link else 0x14000000)|(((t-a)//4)&0x3ffffff)
def adrp(pc,reg,target):
 d=(target>>12)-(pc>>12);return 0x90000000|reg|((d&3)<<29)|(((d>>2)&0x7ffff)<<5)
patch(0x1bb94,[br(0x1bb94,0x7fd0)])
patch(0x7fd0,[0x2a1403e1,br(0x7fd4,0x7f94,True),br(0x7fd8,0x1bd38)])
patch(0xccec,[0x91000021|(0x184<<10)])
patch(0xcd18,[adrp(0xcd18,1,0x1be44),0x91000021|(0xe44<<10)])
m=struct.unpack_from('<I',b,4)[0];assert m+struct.unpack_from('<I',b,m+12)[0]==0x59020
patch(m+12,[0x59040-m])
Path('work/d11/d11.bin').write_bytes(b);Path('work/d11/changes.json').write_text(json.dumps(ranges))
