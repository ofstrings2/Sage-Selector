exec(open('work/decode_donors.py').read().split('D=Path')[0])
import shutil,zipfile
import subprocess
W=Path('work/d08');BASE=0x1bb00
s='''entry:
stp x29,x30,[sp,#-0x90]!
mov x29,sp
stp x19,x20,[sp,#0x10]
stp x21,x22,[sp,#0x20]
stp x23,x24,[sp,#0x30]
adr x24, entry
sub x24,x24,#0x1b,lsl #12
sub x24,x24,#0xb00
add x8,x24,#0x23,lsl #12
add x8,x8,#0x70
ldr w20,[x8,#0x20]
cmp w20,#7
b.hi search
ldr w9,[x8,w20,uxtw #2]
cmp w9,w1
b.eq mapped
search:
mov w20,#0
loop:
ldr w9,[x8,w20,uxtw #2]
cmp w9,w1
b.eq mapped
add w20,w20,#1
cmp w20,#8
b.lo loop
b done
mapped:
add x10,x24,#0x3d,lsl #12
add x10,x10,#0x6f8
stlr w1,[x10]
'''
for slot in [0,2,3,4,6]:s+=f'cmp w20,#{slot}\nb.eq slot{slot}\n'
s+='b done\n'
def mov32(r,v):return f'movz {r},#{v&65535}\nmovk {r},#{v>>16},lsl #16\n'
for slot,idx,h in [(0,0,0x8c63f616),(2,1,0x4dd38161),(3,4,0x15576a07),(4,2,0xd21b65b6),(6,3,0x361877c4)]:
 s+=f'slot{slot}:\nmov w22,#{idx}\n'+mov32('w23',h)+'b resolve\n'
s+='''resolve:
add x8,x24,#0x40,lsl #12
ldr x8,[x8,#0x568]
cbz x8,done
ldr x21,[x8,#0x48]
cbz x21,done
'''+mov32('w9',0x462e3d8)+'''ldr x8,[x21,x9]
cbz x8,done
ldr x19,[x8]
cbz x19,done
stp xzr,xzr,[sp,#0x40]
stp xzr,xzr,[sp,#0x50]
stp xzr,xzr,[sp,#0x60]
strb wzr,[sp,#0x70]
mov x0,x19
add x1,sp,#0x40
'''+mov32('w2',0x060890b0)
def call(a):return mov32('w9',a)+'add x8,x21,x9\nblr x8\n'
s+=call(0xddbb04)+'tbz w0,#0,done\n'
s+='mov x0,x19\nadd x1,sp,#0x50\nadd x2,sp,#0x40\n'+mov32('w3',0x42026d93)+call(0x80e6c4)+'tbz w0,#0,done\n'
s+='mov x0,x19\nadd x1,sp,#0x60\nadd x2,sp,#0x50\nmov w3,w23\n'+call(0x80e6c4)+'tbz w0,#0,done\n'
s+='mov x0,x19\nadd x1,sp,#0x70\nadd x2,sp,#0x60\n'+mov32('w3',0xe2d35fd8)+call(0x92a3e4)+'tbz w0,#0,done\n'
s+=mov32('w9',0x462e180)+'''ldr x8,[x21,x9]
cbz x8,done
ldr x0,[x8]
cbz x0,done
mov w1,#0x12
'''+call(0xf68af0)+'''cbz x0,done
mov x19,x0
ldrb w8,[sp,#0x70]
cmp w8,#0
cset w2,eq
mov x0,x19
mov w1,w22
'''+call(0x196110c)+'''ldrb w8,[sp,#0x70]
cbz w8,done
mov x0,x19
mov w1,w22
mov w2,#1
'''+call(0x92a8cc)+'''done:
mov w0,#0
ldp x23,x24,[sp,#0x30]
ldp x21,x22,[sp,#0x20]
ldp x19,x20,[sp,#0x10]
ldp x29,x30,[sp],#0x90
ret
'''
(W/'dispatcher.s').write_text(s)
subprocess.run(['clang','-target','aarch64-none-elf','-c',str(W/'dispatcher.s'),'-o',str(W/'dispatcher.o')],check=True)
e=(W/'dispatcher.o').read_bytes();shoff=struct.unpack_from('<Q',e,40)[0];ents,n,si=struct.unpack_from('<HHH',e,58)
sections=[struct.unpack_from('<IIQQQQIIQQ',e,shoff+i*ents) for i in range(n)]
t=sections[si];names=e[t[4]:t[4]+t[5]]
for sec in sections:
 name=names[sec[0]:].split(b'\0')[0]
 if name==b'.text':payload=e[sec[4]:sec[4]+sec[5]]
 assert not (sec[1] in (4,9) and sec[5]),'Unresolved ELF relocation'
assert BASE+len(payload)<=0x1c000
original=Path('work/d07/d07.bin').read_bytes();raw=bytearray(original);raw[BASE:BASE+len(payload)]=payload
intercept=struct.pack('<4I',0x2a1303e1,0x94000000|(((BASE-0x7c6c)//4)&0x3ffffff),0x52800001,0x14000000|(((0x7c54-0x7c74)//4)&0x3ffffff))
raw[0x7c68:0x7c78]=intercept
# Remove only the two playback-only hook installations. Pause hooks stay.
for at in [0xcbf0,0xccc4]:
 assert struct.unpack_from('<I',raw,at)[0]&0xfc000000==0x94000000
 struct.pack_into('<I',raw,at,0xd2800000) # mov x0, #0; no installed trampoline
# Remove audio-delay hook and animation-update hook bodies, now unregistered.
for a,b in [(0x7770,0x78b0),(0x8ea0,0x90e0)]:raw[a:b]=bytes(b-a)
# Disable emote-only music stop and forced AS reset helpers. Their callers
# in the shared state machine remain, but these helpers now have no side effects.
for a,b in [(0x7f90,0x8050),(0x8180,0x8280)]:
 raw[a:b]=bytes(b-a);struct.pack_into('<I',raw,a,0xd65f03c0)
# Old emote execute body is unreachable after the validated D07 interception.
raw[0x7c78:0x7d5c]=bytes(0x7d5c-0x7c78)
raw[0x7d70:0x7d80]=bytes(0x10)
# Keep config loading, persistence plumbing, pause cleanup and wheel tick.
# Skip only the Down-HUD texture lookup/show-hide loop.
at=0xbe18;to=0xbf04
struct.pack_into('<I',raw,at,0x14000000|(((to-at)//4)&0x3ffffff))
source=Path('work/donors/EmoteWheel/exefs/subsdk4').read_bytes();header=bytearray(source[:256]);body=bytearray();segs=json.loads(Path('work/decoded/emote.json').read_text())['segments'];oldsize=segs[0][1];segs[0][1]=BASE+len(payload)
for i,(va,size) in enumerate(segs):
 data=bytes(raw[va:va+size]);compressed=lz4.block.compress(data,store_size=False,mode='high_compression',compression=12)
 struct.pack_into('<III',header,0x10+16*i,256+len(body),va,size)
 struct.pack_into('<I',header,0x60+4*i,len(compressed));header[0xa0+32*i:0xc0+32*i]=hashlib.sha256(data).digest();body.extend(compressed)
header[0x40:0x60]=hashlib.sha256(raw).digest()
out=W/'build'/'Sage Wheel v0.2 D08';(out/'exefs').mkdir(parents=True,exist_ok=True);shutil.copy2('work/donors/EmoteWheel/exefs/main.npdm',out/'exefs/main.npdm')
(out/'exefs/subsdk4').write_bytes(header+body);(W/'d08.bin').write_bytes(raw);(W/'payload.bin').write_bytes(payload)
md=capstone.Cs(capstone.CS_ARCH_ARM64,capstone.CS_MODE_ARM)
(W/'dispatcher.asm').write_text('\n'.join(f'{x.address:08x} {x.mnemonic} {x.op_str}' for x in md.disasm(payload,BASE)))
assert raw[0x8280:0x8ea0]==original[0x8280:0x8ea0] and raw[0x90e0:0x9d80]==original[0x90e0:0x9d80]
assert raw[0x2000:0x5000]==original[0x2000:0x5000]
assert raw[0x1c000:]==original[0x1c000:]
print('payload',hex(BASE),hex(BASE+len(payload)),len(payload),'old text end',hex(oldsize),'new file',len(header+body))
