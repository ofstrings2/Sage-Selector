typedef unsigned long U;
extern char __module_start[];
#define V(t,o) (*(volatile t*)(__module_start+(o)))
#define SEC(n) __attribute__((section(n),noinline))
extern void old_utility(void*,unsigned);
static const char event_name[] __attribute__((section(".event_name")))="DmT_OP_GanonWakeUp_PreRender_Memory";
SEC(".memory") void memory(void){
 if(V(U,0x59008))return; // Keep mounted action ownership untouched.
 U m=V(U,0x40568);if(!m)return;m=*(U*)(m+0x48);if(!m)return;
 U p=*(U*)(m+0x462e3e8);if(!p)return;U mgr=*(U*)p;if(!mgr)return;
 _Alignas(16) unsigned char arg[0x1b20];const char*name=event_name;
 ((void(*)(void*))(m+0x10229b0))(arg);
 ((void(*)(void*,const char**,int))(m+0xb51c14))(arg+0x1a90,&name,-1);
 ((int(*)(U,void*))(m+0x11f0700))(mgr,arg);
 ((void(*)(void*))(m+0x76eb88))(arg+0x1968);
 ((void(*)(void*))(m+0x76eb88))(arg+0x1950);
}
SEC(".new_utility") void new_utility(void*as,unsigned slot){if(slot==1)memory();else old_utility(as,slot);}
