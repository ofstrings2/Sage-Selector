typedef unsigned long U;typedef unsigned W;
extern char __module_start[];
#define V(t,o) (*(volatile t*)(__module_start+(o)))
#define SEC(n) __attribute__((section(n),noinline))
extern int hid(U*);extern U ticks(void);extern void mounted_poll(void);extern void cancel(void);
// Native Actor pause reasons occupy bits 11..16. Accept reason 1 alone.
SEC(".gate") U reason_one(void){
 U as=V(U,0x57ec8);if(!as)return 0;U actor=*(U*)(as+0x18);if(!actor)return 0;
 return ((*(W*)(actor+0x28)&0x1f800)==0x1000)?as:0;
}
SEC(".start") void start_cull(U as){
 V(U,0x59000)=as;V(unsigned char,0x57f38)=0;V(unsigned char,0x57f41)=0;
 V(U,0x57f48)=ticks();V(W,0x59040)=1;V(W,0x59010)=1;V(W,0x57f58)=1;
}
SEC(".eligible") U eligible(void){
 if(V(W,0x59010)||V(W,0x57f58)||!V(unsigned char,0x576b0)||V(unsigned char,0x57f40)||V(unsigned char,0x57ef0))return 0;
 return reason_one();
}
SEC(".hud") void cull_tick(void){
 U b=0;W down=hid(&b)&&((b>>15)&1);W previous=V(W,0x59044);V(W,0x59044)=down;
 if(V(W,0x59040)){
  if(!V(W,0x59010))V(W,0x59040)=0;
  else if((V(unsigned char,0x57ef0)&&V(W,0x57f58)==1)||!reason_one()) {cancel();V(W,0x59040)=0;}
 }else if(down&&!previous&&!(b&2)) {U as=eligible();if(as)start_cull(as);}
 mounted_poll();
}
