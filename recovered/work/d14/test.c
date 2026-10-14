#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
typedef uint64_t U;typedef uint32_t W;
static unsigned char *m,*g;static unsigned char as[64],player[0x240],components[0x240],equipment[0x100],actors[8][0x40];
static int checked,resolved,slept,prior,mode;static unsigned seen;
#define M(o) (*(U*)(m+(o)))
static unsigned idx(void*p){U d=(unsigned char*)p-(equipment+0x20);assert(d%0x18==0&&d/0x18<8);return d/0x18;}
static int valid(void*p){unsigned i=idx(p);checked++;return mode==1?0:((i&1)==0);}
static void* resolve(void*p,void*z,int flag){assert(!z&&flag==1);resolved++;return mode==2?0:actors[idx(p)];}
static void sleep_request(void*p,unsigned reason){assert(!reason);unsigned i=((unsigned char*)p-actors[0])/0x40;assert(i<8&&!(i&1));seen|=1U<<i;slept++;}
static void old(void*p,unsigned slot){assert(p==as&&slot!=7);prior++;}
static void stub(unsigned char*b,U at,void*p){W code[]={0x58000050,0xd61f0200};memcpy(b+at,code,8);memcpy(b+at+8,&p,8);}
static void reset(void){checked=resolved=slept=prior=0;seen=0;mode=0;*(U*)(as+0x18)=(U)player;*(U*)(player+0x228)=(U)components;*(U*)(components+0x230)=(U)equipment;M(0x40568)=(U)(m+0x39000);M(0x39048)=(U)g;}
int main(void){m=mmap(0,0x60000,3,MAP_PRIVATE|MAP_ANON,-1,0);g=mmap(0,0x2000000,3,MAP_PRIVATE|MAP_ANON,-1,0);assert(m!=MAP_FAILED&&g!=MAP_FAILED);FILE*f=fopen("work/d14/d14.bin","rb");assert(f&&fread(m,1,0x60000,f)>0x40000);fclose(f);f=fopen("work/decoded/vanilla.bin","rb");assert(f);fseek(f,0xfa7f08,SEEK_SET);assert(fread(g+0xfa7f08,1,24,f)==24);fclose(f);
stub(g,0x9ee828,valid);stub(g,0x67e8c8,resolve);stub(g,0x83ac04,sleep_request);stub(m,0x1bf08,old);__builtin___clear_cache((char*)m,(char*)m+0x20000);__builtin___clear_cache((char*)g,(char*)g+0x2000000);assert(!mprotect(m,0x20000,5));assert(!mprotect(g,0x2000000,5));void(*utility)(void*,unsigned)=(void*)(m+0x1bfd8);
reset();for(unsigned i=0;i<8;i++)if(i!=7)utility(as,i);assert(prior==7&&!checked&&!slept);
reset();utility(as,7);assert(checked==8&&resolved==4&&slept==4&&seen==0x55&&!prior);
reset();mode=1;utility(as,7);assert(checked==8&&!resolved&&!slept);
reset();mode=2;utility(as,7);assert(checked==8&&resolved==4&&!slept);
for(int null=0;null<6;null++){reset();switch(null){case 0:break;case 1:*(U*)(as+0x18)=0;break;case 2:M(0x40568)=0;break;case 3:M(0x39048)=0;break;case 4:*(U*)(player+0x228)=0;break;case 5:*(U*)(components+0x230)=0;break;}utility(null?as:0,7);assert(!checked&&!resolved&&!slept);}
puts("PASS D14 native AArch64: slot 7 only, exact native EquipmentUser getter, eight dynamic links, validity/null guards, native sleep reason 0 ABI; seven other slots forwarded unchanged.");}
