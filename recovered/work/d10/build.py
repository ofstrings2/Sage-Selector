exec(open('work/decode_donors.py').read().split('D=Path')[0])
import shutil,subprocess
W=Path('work/d10');raw=bytearray((W/'linked.bin').read_bytes());base=Path('work/d08/d08.bin').read_bytes();edits=[]
def patch(a,words):
 data=struct.pack('<'+'I'*len(words),*words);raw[a:a+len(data)]=data;edits.append([a,a+len(data)])
def branch(a,to,link=True):return (0x94000000 if link else 0x14000000)|(((to-a)//4)&0x3ffffff)
# Reuse exactly the two installations D08 disabled; retain trampoline storage.
# Audio hook -> ExecutePlayerRideRobot update, callback mounted_update at8ea0.
patch(0xcbc0,[0xd2800002|((0x1d7cb8c&65535)<<5),0xf2a00002|((0x1d7cb8c>>16)<<5)])
patch(0xcbc8,[0x90000001|((((0x8000>>12)-(0xcbc8>>12))&3)<<29)|(((((0x8000>>12)-(0xcbc8>>12))>>2)&0x7ffff)<<5),0x91000021|(0xea0<<10)])
patch(0xcbf0,[branch(0xcbf0,0x1bd0)])
# AS hook -> ExecutePlayerRideRobot end at1d7d8ac; callback7770.
patch(0xccb0,[0x90000001|((((0x7000>>12)-(0xccb0>>12))&3)<<29)|(((((0x7000>>12)-(0xccb0>>12))>>2)&0x7ffff)<<5)])
patch(0xccb8,[0x91000021|(0x770<<10),0x91400000|(0x1d7d<<10),0x91000000|(0x8ac<<10),branch(0xccc4,0x1bd0)])
# Poll adapter on the existing HUD update, which still calls original wheel tick.
patch(0xbd60,[branch(0xbd60,0x1bd50)])
# Dedicated zero-initialized adapter state, outside all original globals.
mod=struct.unpack_from('<I',raw,4)[0];assert raw[mod:mod+4]==b'MOD0';bssend=mod+struct.unpack_from('<I',raw,mod+12)[0];assert bssend==0x59000,hex(bssend)
patch(mod+12,[0x59020-mod])
source=Path('work/d08/build/Sage Wheel v0.2 D08/exefs/subsdk4').read_bytes();header=bytearray(source[:256]);body=bytearray();assert struct.unpack_from('<I',header,0x3c)[0]==0x18828
struct.pack_into('<I',header,0x3c,0x18848)
for i in range(3):
 _,va,size=struct.unpack_from('<III',header,0x10+16*i)
 if i==0:size=0x1be44
 data=bytes(raw[va:va+size]);packed=lz4.block.compress(data,store_size=False,mode='high_compression',compression=12)
 struct.pack_into('<III',header,0x10+16*i,256+len(body),va,size);struct.pack_into('<I',header,0x60+4*i,len(packed));header[0xa0+32*i:0xc0+32*i]=hashlib.sha256(data).digest();body.extend(packed)
header[0x40:0x60]=hashlib.sha256(raw).digest()
name='Sage Wheel v0.2 D10 Mounted Input';out=W/'build'/name
shutil.copytree('work/d08/build/Sage Wheel v0.2 D08',out,dirs_exist_ok=True)
(out/'exefs/subsdk4').write_bytes(header+body);(W/'d10.bin').write_bytes(raw)
p=out/'romfs/EmoteConfig/emotes.json';cfg=json.loads(p.read_text());e=next(v for v in cfg['emotes'].values() if v['Name']=='Warp');assert e['Bntx']=='Obj_Warp';e['Bntx']='Obj_WarpDLC_Prototype';p.write_text(json.dumps(cfg,indent=2)+'\n')
allowed=edits+json.loads((W/'ranges.json').read_text());assert all(any(a<=i<b for a,b in allowed) for i,(x,y) in enumerate(zip(raw,base)) if x!=y)
assert raw[0x1bb00:0x1bd50]==base[0x1bb00:0x1bd50];assert raw[0x2000:0x5000]==base[0x2000:0x5000];assert raw[0x1c000:]==base[0x1c000:]
(W/'changes.json').write_text(json.dumps(allowed));md=capstone.Cs(capstone.CS_ARCH_ARM64,capstone.CS_MODE_ARM)
(W/'changes.asm').write_text('\n\n'.join('\n'.join(f'{i.address:08x} {i.mnemonic} {i.op_str}' for i in md.disasm(raw[a:b],a)) for a,b in allowed if a>0x100))
print('Built',out,'NSO',len(header+body),'BSS',hex(bssend),'->0x59020')
