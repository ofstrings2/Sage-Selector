// D14: native sleep reason 0 on Link's currently linked dynamic equipment.
typedef unsigned long U;
extern char __module_start[];
#define V(t,o) (*(volatile t*)(__module_start+(o)))
#define SEC(n) __attribute__((section(n),noinline))
extern void previous_utility(void*,unsigned);
SEC(".slot") void sleep_slot(U main,void*link){
 if(!((int(*)(void*))(main+0x9ee828))(link))return;
 void*actor=((void*(*)(void*,void*,int))(main+0x67e8c8))(link,0,1);
 if(actor)((void(*)(void*,unsigned))(main+0x83ac04))(actor,0);
}
SEC(".sleep") void sleep_equipment(void*as){
 if(!as)return;U actor=*(U*)((char*)as+0x18);if(!actor)return;
 U m=V(U,0x40568);if(!m)return;m=*(U*)(m+0x48);if(!m)return;
 U equip=((U(*)(U))(m+0xfa7f08))(actor);if(!equip)return;
 for(unsigned i=0;i<8;i++)sleep_slot(m,(void*)(equip+0x20+0x18*i));
}
SEC(".utility") void utility(void*as,unsigned slot){if(slot==7)sleep_equipment(as);else previous_utility(as,slot);}
