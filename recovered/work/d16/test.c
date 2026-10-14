#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
typedef uint64_t U;typedef uint32_t W;
static unsigned char *m,*g,as[64],player[0x240],components[0x240],equipment[0x100],actors[8][0x40];
static int checked,resolved,slept,woken,prior,mode;static unsigned present,seen;
#define M(o) (*(U*)(m+(o)))
#define FLAGS(i) (*(W*)(actors[i]+0x28))
#define LIFE(i) (*(W*)(actors[i]+0x24))
static unsigned idx(void*p){U d=(unsigned char*)p-(equipment+0x20);assert(d%0x18==0&&d/0x18<8);return d/0x18;}
static unsigned actoridx(void*p){U d=(unsigned char*)p-actors[0];assert(d%0x40==0&&d/0x40<8);return d/0x40;}
static int valid(void*p){checked++;return (present>>idx(p))&1;}
static void* resolve(void*p,void*z,int flag){assert(!z&&flag==1);resolved++;return mode?0:actors[idx(p)];}
static void sleep_request(void*p,unsigned reason){unsigned i=actoridx(p);assert(reason==0&&((present>>i)&1));seen|=1U<<i;slept++;FLAGS(i)|=1;}
static int wake_request(void*p,unsigned mask,void*param){unsigned i=actoridx(p);assert(mask==0x7ff&&((present>>i)&1));assert(!((U)param&15));for(int j=0;j<0x50;j++)assert(!((unsigned char*)param)[j]);seen|=1U<<i;woken++;FLAGS(i)&=~mask;return 1;}
static void old(void*p,unsigned slot){assert(p==as&&slot!=7);prior++;}
static void stub(unsigned char*b,U at,void*p){W code[]={0x58000050,0xd61f0200};memcpy(b+at,code,8);memcpy(b+at+8,&p,8);}
static void counts(void){checked=resolved=slept=woken=prior=0;seen=0;}
static void reset(void){counts();present=0;mode=0;memset(actors,0,sizeof(actors));for(int i=0;i<8;i++)LIFE(i)=2;*(U*)(as+0x18)=(U)player;*(U*)(player+0x228)=(U)components;*(U*)(components+0x230)=(U)equipment;M(0x40568)=(U)(m+0x39000);M(0x39048)=(U)g;}
int main(void){m=mmap(0,0x60000,3,MAP_PRIVATE|MAP_ANON,-1,0);g=mmap(0,0x2000000,3,MAP_PRIVATE|MAP_ANON,-1,0);assert(m!=MAP_FAILED&&g!=MAP_FAILED);FILE*f=fopen("work/d16/d16.bin","rb");assert(f&&fread(m,1,0x60000,f)>0x40000);fclose(f);f=fopen("work/decoded/vanilla.bin","rb");assert(f);fseek(f,0xfa7f08,SEEK_SET);assert(fread(g+0xfa7f08,1,24,f)==24);fclose(f);stub(g,0x9ee828,valid);stub(g,0x67e8c8,resolve);stub(g,0x83ac04,sleep_request);stub(g,0xaedc50,wake_request);stub(m,0x1bf08,old);__builtin___clear_cache((char*)m,(char*)m+0x20000);__builtin___clear_cache((char*)g,(char*)g+0x2000000);assert(!mprotect(m,0x20000,5));assert(!mprotect(g,0x2000000,5));void(*utility)(void*,unsigned)=(void*)(m+0x1bfd8);
reset();for(unsigned i=0;i<8;i++)if(i!=7)utility(as,i);assert(prior==7&&!checked&&!slept&&!woken);
// Every assignment of empty, awake, asleep across all eight equipped links.
for(unsigned c=0;c<6561;c++){reset();unsigned n=c,any=0,count=0;for(int i=0;i<8;i++,n/=3){unsigned v=n%3;if(v){present|=1U<<i;count++;}FLAGS(i)=0x1000|(v==2?1:0);any|=v==2;}utility(as,7);assert(checked==8&&resolved==count&&seen==present);assert(woken==(any?count:0)&&slept==(any?0:count));for(int i=0;i<8;i++){assert(FLAGS(i)&0x1000);if((present>>i)&1)assert((FLAGS(i)&0x7ff)==(any?0:1));}}
// Equipment changes between activations: one item sleeps, new awake item joins, both wake.
reset();present=1U<<4;utility(as,7);assert(slept==1&&FLAGS(4)==1);counts();present|=1;utility(as,7);assert(woken==2&&!slept&&!FLAGS(0)&&!FLAGS(4));counts();utility(as,7);assert(slept==2&&!woken&&FLAGS(0)==1&&FLAGS(4)==1);
// Every native sleep reason controls direction; non-sleep flags do not.
for(int reason=0;reason<11;reason++){reset();present=3;FLAGS(0)=1U<<reason;utility(as,7);assert(woken==2&&!slept&&!FLAGS(0)&&!FLAGS(1));}
reset();present=1;FLAGS(1)=1;utility(as,7);assert(slept==1&&!woken&&FLAGS(1)==1); // unequipped actor ignored
reset();present=3;LIFE(0)=7;FLAGS(0)=1;utility(as,7);assert(slept==1&&!woken&&seen==2&&FLAGS(0)==1); // unsupported lifecycle ignored
reset();present=255;mode=1;utility(as,7);assert(checked==8&&resolved==8&&!slept&&!woken);
for(int null=0;null<6;null++){reset();switch(null){case 0:break;case 1:*(U*)(as+0x18)=0;break;case 2:M(0x40568)=0;break;case 3:M(0x39048)=0;break;case 4:*(U*)(player+0x228)=0;break;case 5:*(U*)(components+0x230)=0;break;}utility(null?as:0,7);assert(!checked&&!resolved&&!slept&&!woken);}
puts("PASS 6,561 equipment-state combinations, newly equipped item/mixed-state normalization, all 11 native sleep reasons, empty/invalid/unequipped actor exclusions, unchanged pause bits, null guards, native call ABI and seven unchanged utility routes (mocked native sleep/wake services).");}
