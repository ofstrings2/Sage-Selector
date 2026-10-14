#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
typedef uint64_t U;typedef uint32_t W;
static volatile int busy,held;static unsigned char special[0x100];
static int native_busy(void*p){return busy;}
static int native_slot(void*p,U slot){assert(slot<8);return held;}
static void* native_special(void*p){return special;}
static void stub(unsigned char*m,U a,void*f){W op[]={0x58000050,0xd61f0200};memcpy(m+a,op,8);memcpy(m+a+8,&f,8);}
int main(void){
 unsigned char*m=mmap(0,0x5000000,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANON,-1,0);assert(m!=MAP_FAILED);
 FILE*f=fopen("work/decoded/vanilla.bin","rb");assert(f);fread(m,1,0x5000000,f);fclose(f);
 assert(*(W*)(m+0x931bac)==0xd280002b);stub(m,0x11e0a30,native_busy);stub(m,0x931f30,native_slot);stub(m,0x85c57c,native_special);
 __builtin___clear_cache((char*)m,(char*)m+0x2b1a000);assert(!mprotect(m,0x2b1c000,PROT_READ|PROT_EXEC));
 unsigned char*p=calloc(1,0x2000),*components=calloc(1,0x2000),*state=calloc(1,0x2000),*input=calloc(1,0x100),*bsa=calloc(1,0x400),*action=calloc(1,0x100),*sub=calloc(1,0x100);
 *(U*)(p+0x228)=(U)components;*(U*)(components+0x3a8)=(U)state;*(U*)(components+0x230)=0x12340000;*(U*)(components+0x158)=(U)bsa;
 *(U*)(state+0x18)=(U)p;*(U*)(state+0x38)=(U)input;*(U*)(bsa+0x1f0)=(U)action;*(U*)(bsa+0x1f8)=(U)sub;
 int(*gate)(void*)=(void*)(m+0x931b20);int original[300][2][4],changes=0;
 for(int pass=0;pass<2;pass++){
  if(pass){size_t page=getpagesize();U a=0x931bac&~(page-1);assert(!mprotect(m+a,page,PROT_READ|PROT_WRITE));*(W*)(m+0x931bac)=0xd284002b;__builtin___clear_cache((char*)m+a,(char*)m+a+page);assert(!mprotect(m+a,page,PROT_READ|PROT_EXEC));}
  for(int action_id=0;action_id<300;action_id++)for(int variant=0;variant<2;variant++)for(int flags=0;flags<4;flags++){
   *(W*)(action+0x28)=variant?0x11c:action_id;*(W*)(action+0x4c)=action_id;
   input[2]=flags&1?4:0;state[0xad8]=flags&2?1:0;int result=gate(p);
   if(!pass)original[action_id][variant][flags]=result;
   else if(result!=original[action_id][variant][flags]){assert(action_id==25&&flags==1&&result==1);changes++;}
  }
 }
 assert(changes==2);
 *(W*)(action+0x28)=25;input[2]=0;state[0xad8]=0;assert(!gate(p));state[0x23]=1;assert(gate(p));state[0x23]=0;input[2]=4;
 state[0xae3]=8;assert(!gate(p));state[0xae3]=0;
 busy=1;held=0;assert(!gate(p));held=1;assert(gate(p));
 printf("PASS 4800 native predicate calls: only RideRobot 25 changes eligibility, including wrapped action; input and blocking flags remain effective. Additional alternate-input/blocking-path checks passed.\n");
}
