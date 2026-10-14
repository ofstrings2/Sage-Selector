entry:
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
cmp w20,#0
b.eq slot0
cmp w20,#2
b.eq slot2
cmp w20,#3
b.eq slot3
cmp w20,#4
b.eq slot4
cmp w20,#6
b.eq slot6
b done
slot0:
mov w22,#0
movz w23,#62998
movk w23,#35939,lsl #16
b resolve
slot2:
mov w22,#1
movz w23,#33121
movk w23,#19923,lsl #16
b resolve
slot3:
mov w22,#4
movz w23,#27143
movk w23,#5463,lsl #16
b resolve
slot4:
mov w22,#2
movz w23,#26038
movk w23,#53787,lsl #16
b resolve
slot6:
mov w22,#3
movz w23,#30660
movk w23,#13848,lsl #16
b resolve
resolve:
add x8,x24,#0x40,lsl #12
ldr x8,[x8,#0x568]
cbz x8,done
ldr x21,[x8,#0x48]
cbz x21,done
movz w9,#58328
movk w9,#1122,lsl #16
ldr x8,[x21,x9]
cbz x8,done
ldr x19,[x8]
cbz x19,done
stp xzr,xzr,[sp,#0x40]
stp xzr,xzr,[sp,#0x50]
stp xzr,xzr,[sp,#0x60]
strb wzr,[sp,#0x70]
mov x0,x19
add x1,sp,#0x40
movz w2,#37040
movk w2,#1544,lsl #16
movz w9,#47876
movk w9,#221,lsl #16
add x8,x21,x9
blr x8
tbz w0,#0,done
mov x0,x19
add x1,sp,#0x50
add x2,sp,#0x40
movz w3,#28051
movk w3,#16898,lsl #16
movz w9,#59076
movk w9,#128,lsl #16
add x8,x21,x9
blr x8
tbz w0,#0,done
mov x0,x19
add x1,sp,#0x60
add x2,sp,#0x50
mov w3,w23
movz w9,#59076
movk w9,#128,lsl #16
add x8,x21,x9
blr x8
tbz w0,#0,done
mov x0,x19
add x1,sp,#0x70
add x2,sp,#0x60
movz w3,#24536
movk w3,#58067,lsl #16
movz w9,#41956
movk w9,#146,lsl #16
add x8,x21,x9
blr x8
tbz w0,#0,done
movz w9,#57728
movk w9,#1122,lsl #16
ldr x8,[x21,x9]
cbz x8,done
ldr x0,[x8]
cbz x0,done
mov w1,#0x12
movz w9,#35568
movk w9,#246,lsl #16
add x8,x21,x9
blr x8
cbz x0,done
mov x19,x0
ldrb w8,[sp,#0x70]
cmp w8,#0
cset w2,eq
mov x0,x19
mov w1,w22
movz w9,#4364
movk w9,#406,lsl #16
add x8,x21,x9
blr x8
ldrb w8,[sp,#0x70]
cbz w8,done
mov x0,x19
mov w1,w22
mov w2,#1
movz w9,#43212
movk w9,#146,lsl #16
add x8,x21,x9
blr x8
done:
mov w0,#0
ldp x23,x24,[sp,#0x30]
ldp x21,x22,[sp,#0x20]
ldp x19,x20,[sp,#0x10]
ldp x29,x30,[sp],#0x90
ret
