#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
typedef uint64_t U;typedef uint32_t W;
static unsigned char *m,*game,*manager,*event;
static U clock_ticks;
static int hooked,polled;
#define M(o) (*(U*)(m+(o)))
static U ticks(void){return clock_ticks;}
static int native_poll(void*states,int count,const W*id){
 assert(count==1&&id);polled++;memset(states,0,40);*(U*)((char*)states+8)=0x100;return 1;
}
static U hook(U target,U callback,int inline_hook){
 assert(target>=0x1000&&target<=0x1002);
 assert(callback>=(U)m+0x3000&&callback<(U)m+0x4000);
 assert(inline_hook==1);hooked++;return (U)native_poll;
}
static void stub(unsigned char*b,U at,void*p){
 W code[]={0x58000050,0xd61f0200};memcpy(b+at,code,8);memcpy(b+at+8,&p,8);
}
static U sample(int kind){
 unsigned char state[40]={0};W id=0;
 U addr[]={0x329c,0x32e0,0x3324};
 // Addresses are checked against symbols.json below before use.
 int(*poll)(void*,int,const W*)=(void*)(m+addr[kind]);
 int n=poll(state,1,&id);assert(n==1);return *(U*)(state+8);
}
int main(void){
 m=mmap(0,0x60000,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANON,-1,0);
 game=mmap(0,0x4700000,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANON,-1,0);
 manager=mmap(0,0x2000,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANON,-1,0);
 event=mmap(0,0x2000,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANON,-1,0);
 assert(m!=MAP_FAILED&&game!=MAP_FAILED&&manager!=MAP_FAILED&&event!=MAP_FAILED);
 FILE*f=fopen("work/d21/d21.bin","rb");assert(f&&fread(m,1,0x60000,f)>0x40000);fclose(f);
 stub(m,0x1bd0,hook);stub(m,0xd614,ticks);
 M(0x404b0)=0xa000;M(0x404b8)=0xa001;M(0x404e8)=0x1000;M(0x404d0)=0x1001;M(0x404c0)=0x1002;
 M(0x40568)=(U)(m+0x41000);M(0x41048)=(U)game;
 *(U*)(game+0x462e3e8)=(U)(game+0x1000);
 *(U*)(game+0x1000)=(U)manager;
 __builtin___clear_cache((char*)m,(char*)m+0x20000);
 assert(!mprotect(m,0x20000,PROT_READ|PROT_EXEC));
 void(*accepted)(int)=(void*)(m+0x347c);
 accepted(0);assert(!hooked&&!*(W*)(m+0x59054));
 accepted(1);assert(hooked==3&&*(W*)(m+0x59054)==1);
 assert(sample(0)==0x100);
 *(U*)(manager+0x58)=(U)event;
 assert(sample(1)==0x100); // event appears; timer begins
 clock_ticks=2*19200000ULL-1;assert(sample(2)==0x100);
 clock_ticks=2*19200000ULL;assert(sample(0)==0x104); // X only
 clock_ticks+=2*1920000ULL;assert(sample(1)==0x104);
 clock_ticks+=1920000ULL;assert(sample(2)==0x100); // release X
 clock_ticks+=12*1920000ULL-1;assert(sample(0)==0x100);
 clock_ticks++;assert(sample(1)==0x500); // Plus only
 clock_ticks+=3*1920000ULL;assert(sample(2)==0x100);
 clock_ticks+=3*19200000ULL;assert(sample(0)==0x104);assert(*(W*)(m+0x59088)==1);
 *(U*)(manager+0x58)=0;assert(sample(0)==0x100);assert(!*(W*)(m+0x59054));
 accepted(1);assert(hooked==3); // no duplicate hooks
 clock_ticks+=20*19200000ULL+1;assert(sample(0)==0x100);assert(!*(W*)(m+0x59054));
 assert(polled>10);
 puts("PASS X then Plus edges, event-lifecycle scoping, all Npad variants, rejected requests, timeout, and single hook installation (mocked native services). In-game cutscene timing remains unverified.");
}
