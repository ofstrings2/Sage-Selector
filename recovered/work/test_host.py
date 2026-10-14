from pathlib import Path
s=Path('work/core.c').read_text()
s=s.replace('extern char __module_start[];','char __module_start[0x60000];\nstatic unsigned long simulated_time;\nstatic unsigned long resolve_game(unsigned long);\nstatic unsigned long resolve_self(unsigned long);')
s=s.replace('#define FN(type,off) ((type)(self()+(off)))','#define FN(type,off) ((type)resolve_self(off))')
s=s.replace('#define GAME(type,off) ((type)(mainbase()+(off)))','#define GAME(type,off) ((type)resolve_game(off))')
a=s.index('static u64 ticks(');b=s.index('static int hid(',a);s=s[:a]+'static u64 ticks(void){return simulated_time;}\n'+s[b:]
s+='''
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
static u64 fake_buttons;static int fake_x,fake_y,ncalls,opened,ison;static u64 arguments[32][3];static u8* game;
static void original(void* p){(void)p;}
static u32 style(u32* id){(void)id;return 1;}
static int states(struct Hid*h,int count,u32*id){(void)count;(void)id;*h=(struct Hid){.sample=1,.buttons=fake_buttons,.rx=fake_x,.ry=fake_y,.attr=1};return 1;}
static int root(u64 g,void*p,u32 hash){(void)g;(void)hash;*(u64*)p=1;return 1;}
static int child(u64 g,void*p,void*q,u32 hash){(void)q;return root(g,p,hash);}
static int boolean(u64 g,u8*p,void*q,u32 hash){(void)g;(void)q;assert(hash==0xe2d35fd8);*p=ison;return 1;}
static u64 system_(u64 m,u32 id){(void)m;assert(id==0x12);return 1;}
static void setter(u64 s,u32 idx,u32 v){assert(s==1);arguments[ncalls][0]=0x196110c;arguments[ncalls][1]=idx;arguments[ncalls++][2]=v;}
static void dismiss(u64 s,u32 idx,u32 v){assert(s==1);arguments[ncalls][0]=0x92a8cc;arguments[ncalls][1]=idx;arguments[ncalls++][2]=v;}
static void* allocation(u32 n,void* heap,u32 align){(void)heap;assert(n==0x190&&align==8);return calloc(1,n);}
static u64 resolve_game(u64 off){switch(off){case 0xddbb04:return (u64)root;case 0x80e6c4:return (u64)child;case 0x92a3e4:return (u64)boolean;case 0xf68af0:return (u64)system_;case 0x196110c:return (u64)setter;case 0x92a8cc:return (u64)dismiss;case 0x7fa8f0:return (u64)allocation;}assert(0);return 0;}
static u64 resolve_self(u64 off){switch(off){case 0x1b990:return (u64)style;case 0x1ba00:case 0x1b9d0:case 0x1b9b0:return (u64)states;}assert(0);return 0;}
u64 donor_hook(u64 a,u64 b,int c){(void)a;(void)b;(void)c;return (u64)original;}
void donor_open_step(void){opened++;AT(u32,0x57f58)=3;}
void donor_close_body(int a,int b){(void)a;(void)b;AT(u32,0x57f58)=4;}
void donor_cleanup(void){}
void donor_wheel_open(void*p){(void)p;}
void donor_wheel_update(void*p){(void)p;}
void factory0(void){}void factory1(void){}
int main(void){
 game=calloc(1,0x5000000);assert(game);AT(u64,0x40568)=self()+0x39000;AT(u64,0x39048)=(u64)game;
 *(u64*)(game+0x462e3d8)=(u64)(game+0x4900000);*(u64*)(game+0x4900000)=1;
 *(u64*)(game+0x462e180)=(u64)(game+0x4901000);*(u64*)(game+0x4901000)=1;
 S->ready=1;S->tick_original=(u64)original;u8 node[64]={0};
 const int slots[5]={0,2,3,4,6},idx[5]={0,1,4,2,3};
 for(int i=0;i<5;i++)for(ison=0;ison<2;ison++){
  S->selected=slots[i];ncalls=0;fake_buttons=1u<<11;simulated_time+=10000000;begin(node);assert(S->active==1);
  simulated_time+=1000000;fake_buttons=0;tick(0);assert(ncalls==1+ison&&arguments[0][1]==idx[i]&&arguments[0][2]==!ison);
  if(ison)assert(arguments[1][0]==0x92a8cc&&arguments[1][1]==idx[i]&&arguments[1][2]==1);
  tick(0);assert(ncalls==1+ison);
 }
 puts("PASS five native Sage mappings, both directions, exactly once on tap");
 for(int i=1;i<8;i+=i==1?4:2){S->selected=i;ncalls=0;fake_buttons=1u<<11;begin(node);fake_buttons=0;tick(0);assert(ncalls==0);}
 puts("PASS inert Memory/Horse/Warp");
 S->selected=6;fake_buttons=1u<<11;ncalls=0;simulated_time+=10000000;begin(node);simulated_time+=4799999;tick(0);assert(AT(u32,0x57f58)==1&&ncalls==0);
 simulated_time++;tick(0);assert(AT(u32,0x57f58)==3&&ncalls==0);AT(u32,0x57f50)=3;close_wheel(0,0);assert(S->selected==3&&AT(u32,0x57f58)==0&&!ncalls);fake_buttons=0;tick(0);assert(!ncalls);
 puts("PASS 250ms threshold, no hold execution, commit without execution, persistence");
 fake_buttons=1u<<11;begin(node);AT(u32,0x57f58)=3;AT(u32,0x57f50)=7;close_wheel(1,0);assert(S->selected==3);
 puts("PASS cancel retains previous selection");
 u64 masks[]={0,1u<<6,1u<<10,1u<<15,(1u<<11)|(1u<<10)};for(int i=0;i<5;i++){fake_buttons=masks[i];begin(node);assert(!S->active);}
 puts("PASS non-Minus and simultaneous Plus rejection");
 for(int k=0;k<8;k++)for(int d=-20;d<=20;d++){
  double a=(k*45+d)*3.141592653589793/180;int x=lround(sin(a)*32767),y=lround(cos(a)*32767);assert(octant(x,y,99)==(u32)k);
 }
 for(int k=0;k<8;k++){assert(octant(0,0,k)==(u32)k);double a=(k*45+24)*3.141592653589793/180;assert(octant(lround(sin(a)*32767),lround(cos(a)*32767),k)==(u32)k);a=(k*45+27)*3.141592653589793/180;assert(octant(lround(sin(a)*32767),lround(cos(a)*32767),k)==(u32)((k+1)%8));}
 puts("PASS 328 angular samples, eight octants, dead zone, boundary hysteresis");
 void*p=construct(0);assert(*(u16*)((u64)p+0x1e)==255&&*(u64*)p==(u64)p+0x70&&*(u64*)((u64)p+0x180)==(u64)begin);free(p);
 puts("PASS donor-compatible constructor header/private vtable");
 free(game);return 0;
}
'''
Path('work/test_host.c').write_text(s)
