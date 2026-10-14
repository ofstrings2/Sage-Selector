// TotK 1.2.1 mounted-only input adapter. Original rider update/end always run.
typedef unsigned long U; typedef unsigned W;
extern char __module_start[];
#define P(o) (__module_start+(o))
#define V(type,o) (*(volatile type*)P(o))
#define FN(type,o) ((type)(U)V(U,o))
#define SEC(n) __attribute__((section(n),noinline))
extern int hid(U*); extern U ticks(void); extern int execute(void*,int);
extern void wheel_tick(void); extern void close_wheel(int,int);
#define STATE V(W,0x57f58)
#define OWN V(W,0x59010)
#define PREV V(W,0x59014)
#define CTX V(U,0x59000)
#define NODE V(U,0x59008)
SEC(".cancel") void cancel(void){
 OWN=0;
 if(STATE==2||STATE==3)close_wheel(1,0);
 V(int,0x3d6f0)=-1;STATE=0;V(unsigned char,0x57f40)=1;
}
SEC(".mounted_end") void mounted_end(void*n){
 if(NODE==(U)n){NODE=0;CTX=0;PREV=1;if(OWN)cancel();}
 FN(void(*)(void*),0x465b8)(n);
}
SEC(".mounted_update") void mounted_update(void*n){
 FN(void(*)(void*),0x465d0)(n);
 U b=0;int ok=hid(&b);W down=ok&&((b>>15)&1);W was=PREV;PREV=down;
 if(OWN||STATE||was||!down||!V(unsigned char,0x576b0)||V(unsigned char,0x57f40)||(b&2))return;
 void*as=FN(void*(*)(void*),0x46690)(n);if(!as)return;
 NODE=(U)n;CTX=(U)as;V(U,0x57ec8)=(U)as;
 V(unsigned char,0x57f38)=0;V(unsigned char,0x57f41)=0;
 V(U,0x57f48)=ticks();OWN=1;STATE=1;
}
SEC(".poll") void mounted_poll(void){
 if(OWN){
  int def=-1;
  if(STATE==1){
   U b=0;int ok=hid(&b);
   if(!ok||(b&2)){cancel();goto finish;}
   if(!(b&(1UL<<15)))def=V(int,0x3d6f8);
   else {if(ticks()-V(U,0x57f48)>=9600000)STATE=2;goto finish;}
  }else if(STATE==4){def=__atomic_exchange_n((int*)P(0x3d6f0),-1,__ATOMIC_ACQ_REL);}
  else goto finish;
  // Release adapter ownership before native OFF, which may end the rider action.
  OWN=0;STATE=0;if(def>=0)execute((void*)CTX,def);
 }
 finish:wheel_tick();
}
