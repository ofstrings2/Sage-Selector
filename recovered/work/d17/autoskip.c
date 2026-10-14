typedef unsigned long U;
typedef unsigned W;
extern char __module_start[];
#define V(t,o) (*(volatile t*)(__module_start+(o)))
#define SEC __attribute__((section(".autoskip"),noinline,used))

// These are the game's three Npad polling variants. The donor's own input
// adapter confirms buttons at +8 and one state per call.
typedef int (*Poll)(void*,int,const W*);
enum { INSTALL=0x59050, PHASE=0x59054, FULL=0x59058,
       HAND=0x59060, DUAL=0x59068, START=0x59070,
       EVENT=0x59078, ARM=0x59080 };

static __attribute__((always_inline)) inline U now(void){
 return ((U(*)(void))(__module_start+0xd614))();
}
static __attribute__((always_inline)) inline U active_event(void){
 U d=V(U,0x40568);if(!d)return 0;
 U main=*(U*)(d+0x48);if(!main)return 0;
 U p=*(U*)(main+0x462e3e8);if(!p)return 0;
 U mgr=*(U*)p;if(!mgr)return 0;
 return *(U*)(mgr+0x58);
}
static SEC void add_button(void*states,int count){
 if(!states||count<1||!V(W,PHASE))return;
 U t=now(),armed=V(U,ARM),event=active_event();
 if(t-armed>20UL*19200000UL){V(W,PHASE)=0;return;}
 W phase=V(W,PHASE);
 if(phase==1){
  if(!event)return;
  V(U,EVENT)=event;V(U,START)=t;V(W,PHASE)=2;return;
 }
 if(!event||event!=V(U,EVENT)){V(W,PHASE)=0;return;}
 U elapsed=t-V(U,START);
 // Let the movie and its skip UI initialize before sending a real X edge.
 if(phase==2){if(elapsed<2UL*19200000UL)return;V(U,START)=t;V(W,PHASE)=3;phase=3;elapsed=0;}
 if(phase==3){
  if(elapsed<3UL*1920000UL){*(U*)((char*)states+8)|=1UL<<2;return;}
  V(U,START)=t;V(W,PHASE)=4;return;
 }
 if(phase==4){if(elapsed<12UL*1920000UL)return;V(U,START)=t;V(W,PHASE)=5;phase=5;elapsed=0;}
 if(phase==5){
  if(elapsed<3UL*1920000UL){*(U*)((char*)states+8)|=1UL<<10;return;}
  V(W,PHASE)=6;
 }
}

SEC int poll_full(void*states,int count,const W*id){
 Poll original=(Poll)V(U,FULL);int n=original(states,count,id);add_button(states,n);return n;
}
SEC int poll_hand(void*states,int count,const W*id){
 Poll original=(Poll)V(U,HAND);int n=original(states,count,id);add_button(states,n);return n;
}
SEC int poll_dual(void*states,int count,const W*id){
 Poll original=(Poll)V(U,DUAL);int n=original(states,count,id);add_button(states,n);return n;
}
static SEC int install_hooks(void){
 if(V(W,INSTALL))return V(W,INSTALL)==1;
 U (*hook)(U,U,int)=(U(*)(U,U,int))(__module_start+0x1bd0);
 U targets[3]={V(U,0x404b0),V(U,0x404b8),V(U,0x404c0)};
 U callbacks[3]={(U)poll_full,(U)poll_hand,(U)poll_dual};
 const W slots[3]={FULL,HAND,DUAL};
 for(int i=0;i<3;i++){
  if(!targets[i]){V(W,INSTALL)=2;return 0;}
  U trampoline=hook(targets[i],callbacks[i],1);
  if(!trampoline){V(W,INSTALL)=2;return 0;}
  V(U,slots[i])=trampoline;
 }
 V(W,INSTALL)=1;return 1;
}
SEC void memory_after_request(int accepted){
 if(!accepted)return;
 if(!install_hooks())return;
 V(U,EVENT)=0;V(U,START)=0;V(U,ARM)=now();V(W,PHASE)=1;
}
__attribute__((naked,section(".autoskip"),used))
void memory_request_wrapper(void){
 __asm__ volatile(
  "stp x29, x30, [sp, #-0x10]!\n"
  "mov x29, sp\n"
  "blr x8\n"
  "bl memory_after_request\n"
  "ldp x29, x30, [sp], #0x10\n"
  "ret\n");
}
