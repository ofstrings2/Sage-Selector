.text
.balign 128
.global factory0
factory0:
 stp x8,x9,[sp,#-32]!
 mrs x8,nzcv
 str x8,[sp,#16]
 movz w9,#28665
 movk w9,#9012,lsl #16
 cmp w26,w9
 b.ne unmatched0
 ldr x8,[sp,#16]
 msr nzcv,x8
 ldp x8,x9,[sp],#32
 ldr x0,[sp,#0x28]
 bl construct
 mov x27,x0
 adrp x16,__module_start+0x38000
 ldr x16,[x16,#0x30]
 movz w17,#41236
 movk w17,#0x77,lsl #16
 add x16,x16,x17
 br x16
unmatched0:
 ldr x8,[sp,#16]
 msr nzcv,x8
 ldp x8,x9,[sp],#32
 adrp x16,__module_start+0x38000
 ldr x16,[x16,#0x30]
 movz w17,#41236
 movk w17,#0x77,lsl #16
 add x16,x16,x17
 br x16
.balign 128
.global factory1
factory1:
 stp x8,x9,[sp,#-32]!
 mrs x8,nzcv
 str x8,[sp,#16]
 movz w9,#28665
 movk w9,#9012,lsl #16
 cmp w26,w9
 b.ne unmatched1
 ldr x8,[sp,#16]
 msr nzcv,x8
 ldp x8,x9,[sp],#32
 ldr x0,[sp,#0x28]
 bl construct
 adrp x16,__module_start+0x38000
 ldr x16,[x16,#0x30]
 movz w17,#41948
 movk w17,#0x77,lsl #16
 add x16,x16,x17
 br x16
unmatched1:
 ldr x8,[sp,#16]
 msr nzcv,x8
 ldp x8,x9,[sp],#32
 adrp x16,__module_start+0x38000
 ldr x16,[x16,#0x30]
 movz w17,#41952
 movk w17,#0x77,lsl #16
 add x16,x16,x17
 br x16
