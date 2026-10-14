import sys
sys.path.insert(0,'vendor-python')
import mmh3
h=mmh3.hash('SeqOneShotSageWheelBegin',signed=False)
s='.text\n'
for i in range(2):
 s+=f'''.balign 128
.global factory{i}
factory{i}:
 stp x8,x9,[sp,#-32]!
 mrs x8,nzcv
 str x8,[sp,#16]
 movz w9,#{h&65535}
 movk w9,#{h>>16},lsl #16
 cmp w26,w9
 b.ne unmatched{i}
 ldr x8,[sp,#16]
 msr nzcv,x8
 ldp x8,x9,[sp],#32
 ldr x0,[sp,#0x28]
 bl construct
'''
 if i==0:s+=' mov x27,x0\n'
 s+=f''' adrp x16,__module_start+0x38000
 ldr x16,[x16,#0x30]
 movz w17,#{0xa114 if i==0 else 0xa3dc}
 movk w17,#0x77,lsl #16
 add x16,x16,x17
 br x16
unmatched{i}:
 ldr x8,[sp,#16]
 msr nzcv,x8
 ldp x8,x9,[sp],#32
 adrp x16,__module_start+0x38000
 ldr x16,[x16,#0x30]
 movz w17,#{0xa114 if i==0 else 0xa3e0}
 movk w17,#0x77,lsl #16
 add x16,x16,x17
 br x16
'''
open('work/factory.S','w').write(s)
