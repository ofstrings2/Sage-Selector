from pathlib import Path
s=Path('work/d08/test_integration.c').read_text().replace('work/d08/d08.bin','work/d11/d11.bin').replace('work/d08/build/Sage Wheel v0.2 D08','work/d11/build/Sage Selector D11')
s=s.replace('int main(void){','static int horse_begins,horse_updates;\nstatic void horse_native_begin(unsigned char*n){horse_begins++;assert(n[0x20]==0);}\nstatic void horse_native_update(unsigned char*n){horse_updates++;n[0x20]=1;}\nint main(void){')
end='''
 // D11 native whistle handoff runs on the live native whistle node, never a rider node.
 void(*hb)(void*)=(void*)(mod+0x8184);void(*hu)(void*)=(void*)(mod+0x1be44);
 reset();memset(mod+0x576a0,0,0x900);memset(mod+0x59000,0,0x40);mod[0x576b0]=1;
 M64(0x57ec8)=(U)as;M64(0x46678)=(U)query;M64(0x465a0)=(U)horse_native_begin;M64(0x46598)=(U)horse_native_update;
 for(int j=0;j<8;j++)M32(0x23070+j*4)=j;
 M32(0x23090)=5;M32(0x3d6f8)=5;buttons=1UL<<15;ticks=100;nodes[0x20]=0;
 hb(nodes);hu(nodes);assert(M32(0x57f58)==1&&!horse_begins);
 buttons=0;hu(nodes);assert(horse_begins==1&&M64(0x59020)==(U)nodes&&!nodes[0x20]);
 hu(nodes);assert(horse_updates==1&&nodes[0x20]==1&&!M64(0x59020));
 assert(!sets&&!offs);puts("PASS Horse handoff: native begin once, native update owns completion, no Sage toggle or fabricated node.");
 // A subsequent selector gesture resets whistle ownership and still selects Tulin.
 horse_begins=horse_updates=0;M32(0x3d6f8)=0;M32(0x23090)=0;expected=0;phase=sets=offs=0;on=0;
 buttons=1UL<<15;ticks+=100;hb(nodes);hu(nodes);buttons=0;hu(nodes);assert(sets==1&&!horse_begins&&!horse_updates);
 // Mounted utility dispatch must never launch the on-foot whistle animation on Mineru.
 M64(0x59008)=(U)nodes;M32(0x59028)=0;M32(0x23090)=5;execute(as,5);assert(!M32(0x59028));
 puts("PASS selector after whistle, mounted rider exclusion, and unchanged Sage dispatcher.");
'''
s=s[:s.rfind('}')]+end+'}\n';Path('work/d11/test_integration.c').write_text(s)
