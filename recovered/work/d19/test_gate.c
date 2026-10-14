#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
typedef uint64_t U;typedef uint32_t W;
static unsigned char *m,as[64],actor[128];
#define V(t,o) (*(t*)(m+(o)))
static U buttons,clocktime;static int calls,closes,wheels,valid=1;
static int hid(U*p){*p=buttons;return valid;}
static U ticks(void){return clocktime;}
static void wheel(void){wheels++;}
static int execute(void*p,int d){assert(p==as);assert(d==6);calls++;return 0;}
static void closewheel(int a,int b){assert(a==1&&b==0);closes++;}
static void stub(U a,void*p){W c[]={0x58000050,0xd61f0200};memcpy(m+a,c,8);memcpy(m+a+8,&p,8);}
static void reset(void){memset(m+0x57000,0,0x3000);memset(actor,0,sizeof(actor));memset(as,0,sizeof(as));*(U*)(as+0x18)=(U)actor;*(W*)(actor+0x28)=0x1000;V(U,0x57ec8)=(U)as;V(unsigned char,0x576b0)=1;V(int,0x3d6f8)=6;buttons=0;clocktime=100;calls=closes=wheels=0;valid=1;}
int main(void){m=mmap(0,0x60000,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANON,-1,0);assert(m!=MAP_FAILED);FILE*f=fopen("work/d19/d19.bin","rb");assert(f);assert(fread(m,1,0x60000,f)>0x40000);fclose(f);stub(0x7910,hid);stub(0xd614,ticks);stub(0x8810,wheel);stub(0x7c10,execute);stub(0x85d0,closewheel);__builtin___clear_cache((char*)m,(char*)m+0x20000);assert(!mprotect(m,0x20000,PROT_READ|PROT_EXEC));
U(*gate)(void)=(void*)(m+0x7cfc);void(*tick)(void)=(void*)(m+0x1bf18);
for(W mask=0;mask<64;mask++){reset();*(W*)(actor+0x28)=0xa0000007|(mask<<11);unsigned char copy[128];memcpy(copy,actor,128);assert(gate()==(mask==2?(U)as:0));buttons=1UL<<15;tick();assert(V(W,0x59010)==(mask==2));assert(!memcmp(copy,actor,128));}
puts("PASS all 64 actor pause-reason combinations: only reason 1 alone starts selector; actor bytes unchanged.");
for(int block=0;block<9;block++){reset();buttons=1UL<<15;switch(block){case 0:V(unsigned char,0x57ef0)=1;break;case 1:V(unsigned char,0x57f40)=1;break;case 2:V(unsigned char,0x576b0)=0;break;case 3:V(W,0x57f58)=5;break;case 4:buttons|=2;break;case 5:valid=0;break;case 6:V(W,0x59044)=1;break;case 7:V(U,0x57ec8)=0;break;case 8:*(U*)(as+0x18)=0;break;}tick();assert(!V(W,0x59040)&&!calls);}
puts("PASS existing GamePause, swallow, readiness, busy, B, HID failure, held-input, and null-context guards.");
reset();buttons=1UL<<15;tick();assert(V(W,0x57f58)==1);clocktime+=6719999;tick();assert(V(W,0x57f58)==1);clocktime++;tick();assert(V(W,0x57f58)==2);V(W,0x57f58)=3;V(unsigned char,0x57ef0)=1;tick();assert(V(W,0x59010)==1&&!closes);V(W,0x57f58)=4;V(int,0x3d6f0)=6;buttons=0;tick();assert(calls==1&&!V(W,0x59010)&&!V(W,0x57f58));tick();assert(calls==1&&!V(W,0x59040));
reset();buttons=1UL<<15;tick();buttons=0;tick();assert(calls==1&&!V(W,0x57f58));
for(W state=1;state<=4;state++)for(W mask=0;mask<64;mask++){if(mask==2)continue;reset();buttons=1UL<<15;tick();V(W,0x57f58)=state;V(int,0x3d6f0)=6;*(W*)(actor+0x28)=mask<<11;tick();assert(!calls&&!V(W,0x59010)&&!V(W,0x57f58));assert(closes==(state==2||state==3));}
reset();buttons=1UL<<15;tick();V(unsigned char,0x57ef0)=1;tick();assert(!calls&&!V(W,0x59010));
puts("PASS actual D12 adapter: hold threshold, UI ownership, commit, exactly-once dispatch, tap replay, and cancel on every disallowed reason transition.");
}
