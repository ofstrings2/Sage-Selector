// D15: derive each activation from live equipped actors; no persistent state.
typedef unsigned long U;typedef unsigned W;
extern char __module_start[];
#define V(t,o) (*(volatile t*)(__module_start+(o)))
#define SEC(n) __attribute__((section(n),noinline))
SEC(".resolve") void* resolve(U main,void*link){
 if(!((int(*)(void*))(main+0x9ee828))(link))return 0;
 void*a=((void*(*)(void*,void*,int))(main+0x67e8c8))(link,0,1);
 if(!a || (*(W*)((char*)a+0x24)-1)>5)return 0;
 return a;
}
SEC(".wake") void wake(U main,void*actor){
 _Alignas(16) unsigned char param[0x50]={0};
 ((int(*)(void*,W,void*))(main+0xaedc50))(actor,0x7ff,param);
}
SEC(".toggle") void toggle(U main,U equip){
 void*actors[8];W asleep=0;
 for(W i=0;i<8;i++){
  void*a=resolve(main,(void*)(equip+0x20+0x18*i));actors[i]=a;
  if(a)asleep|=*(W*)((char*)a+0x28)&0x7ff;
 }
 for(W i=0;i<8;i++)if(actors[i]){
  if(asleep)wake(main,actors[i]);
  else ((void(*)(void*,unsigned))(main+0x83ac04))(actors[i],0);
 }
}
SEC(".sleep") void sleep_equipment(void*as){
 if(!as)return;U actor=*(U*)((char*)as+0x18);if(!actor)return;
 U m=V(U,0x40568);if(!m)return;m=*(U*)(m+0x48);if(!m)return;
 U equip=((U(*)(U))(m+0xfa7f08))(actor);if(equip)toggle(m,equip);
}
