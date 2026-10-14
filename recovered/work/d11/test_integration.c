#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
typedef uint64_t U; typedef uint32_t W;
static unsigned char *mod,*game;static int phase,on,expected,sets,offs,fail;static const W hashes[]={0x8c63f616,0x4dd38161,0xd21b65b6,0x361877c4,0x15576a07};
static int root(U g,U *out,W h){assert(g==0x11110000&&h==0x060890b0&&phase++==0);assert(!out[0]&&!out[1]);out[0]=0x111;return fail!=1;}
static int child(U g,U *out,U *parent,W h){assert(g==0x11110000);assert(!out[0]&&!out[1]);if(phase++==1){assert(parent[0]==0x111&&h==0x42026d93);out[0]=0x222;}else{assert(phase==3&&parent[0]==0x222&&h==hashes[expected]);out[0]=0x333;}return fail!=phase;}
static int boolean(U g,unsigned char*out,U *p,W h){assert(g==0x11110000&&p[0]==0x333&&h==0xe2d35fd8&&phase++==3);*out=on;return fail!=4;}
static U system_get(U m,W id){assert(m==0x22220000&&id==0x12&&phase++==4);return fail==5?0:0x33330000;}
static void set(U sys,W idx,W value){assert(sys==0x33330000&&idx==expected&&value==!on&&phase++==5);sets++;}
static void off(U sys,W idx,W value){assert(sys==0x33330000&&idx==expected&&value==1&&on&&phase++==6);offs++;}
static void stub(U at,void*p){W code[]={0x58000050,0xd61f0200};memcpy(game+at,code,8);memcpy(game+at+8,&p,8);}
#define M64(o) (*(U*)(mod+(o)))
#define G64(o) (*(U*)(game+(o)))
#define M32(o) (*(W*)(mod+(o)))
static void reset(void){phase=sets=offs=0;M64(0x46688)=1;M64(0x40568)=(U)(mod+0x39000);M64(0x39048)=(U)game;G64(0x462e3d8)=(U)(game+0x4900000);G64(0x4900000)=0x11110000;G64(0x462e180)=(U)(game+0x4901000);G64(0x4901000)=0x22220000;M32(0x3d6c8)=32;}
static char* readall(const char*path){FILE*f=fopen(path,"rb");assert(f);fseek(f,0,SEEK_END);long n=ftell(f);rewind(f);char*b=calloc(1,n+1);assert(fread(b,1,n,f)==n);fclose(f);return b;}
static U buttons,ticks;static int original_calls;
static int query(void*a,W id){return id==0x12&&((buttons>>15)&1);}
static int hid(U*out){*out=buttons;return 1;}
static U clock_mock(void){return ticks;}
static void log_mock(void){}
static void original_update(unsigned char*n){original_calls++;n[0x20]=1;}
static void modstub(U at,void*p){W code[]={0x58000050,0xd61f0200};memcpy(mod+at,code,8);memcpy(mod+at+8,&p,8);}
static int horse_begins,horse_updates;
static void horse_native_begin(unsigned char*n){horse_begins++;assert(n[0x20]==0);}
static void horse_native_update(unsigned char*n){horse_updates++;n[0x20]=1;}
int main(void){
 mod=mmap(0,0x60000,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANON,-1,0);game=mmap(0,0x5000000,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANON,-1,0);assert(mod!=MAP_FAILED&&game!=MAP_FAILED);
 FILE*f=fopen("work/d11/d11.bin","rb");assert(f);assert(fread(mod,1,0x60000,f)>0x40000);fclose(f);
 U targets[]={0xddbb04,0x80e6c4,0x92a3e4,0xf68af0,0x196110c,0x92a8cc};void* fs[]={root,child,boolean,system_get,set,off};
 for(int i=0;i<6;i++)stub(targets[i],fs[i]);
 modstub(0x7910,hid);modstub(0xd614,clock_mock);modstub(0x7690,log_mock);
 __builtin___clear_cache((char*)mod,(char*)mod+0x20000);__builtin___clear_cache((char*)game,(char*)game+0x2000000);
 assert(!mprotect(mod,0x20000,PROT_READ|PROT_EXEC));size_t page=getpagesize();for(int i=0;i<6;i++)assert(!mprotect(game+(targets[i]&~(page-1)),page,PROT_READ|PROT_EXEC));
 int(*parse)(char*,char*,void*)=(void*)(mod+0xaf20);void*defs=calloc(1,0xe000);
 char*em=readall("work/d11/build/Sage Selector D11/romfs/EmoteConfig/emotes.json");char*wheel=readall("work/d11/build/Sage Selector D11/romfs/EmoteConfig/wheel.json");
 assert(parse(em,wheel,defs)==1);assert(*(W*)((char*)defs+0xd300)==8);
 for(int j=0;j<8;j++)assert(*(W*)((char*)defs+0xd308+j*4)==j);
 puts("PASS exact donor configuration parser accepts D08 files and resolves all eight positions.");
 int(*execute)(void*,int)=(void*)(mod+0x7c10);int map[]={0,-1,1,4,2,-1,3,-1};int permutations[][8]={{0,1,2,3,4,5,6,7},{11,8,17,9,14,12,10,16}};int cases=0;
 for(int p=0;p<2;p++)for(int slot=0;slot<8;slot++)for(on=0;on<2;on++)for(fail=0;fail<6;fail++){
  reset();for(int j=0;j<8;j++)M32(0x23070+j*4)=permutations[p][j];M32(0x23090)=slot;expected=map[slot];
  assert(execute((void*)0x44440000,permutations[p][slot])==0);
  assert(M32(0x3d6f8)==permutations[p][slot]);assert(sets==(expected>=0&&fail==0));assert(offs==(expected>=0&&fail==0&&on));cases++;
 }
 fail=0;on=0;expected=0;reset();for(int j=0;j<8;j++)M32(0x23070+j*4)=j;M32(0x23090)=7;assert(!execute(0,0)&&sets==1);cases++;
 // Duplicates follow the actual committed slot, not first definition match.
 reset();M32(0x23070+3*4)=0;M32(0x23090)=3;expected=4;assert(!execute(0,0)&&sets==1);cases++;
 for(int bad=0;bad<10;bad++){
  reset();for(int j=0;j<8;j++)M32(0x23070+j*4)=j;M32(0x23090)=0;expected=0;int index=0;
  switch(bad){case 0:M64(0x46688)=0;break;case 1:index=-1;break;case 2:index=32;break;case 3:index=20;break;case 4:M64(0x40568)=0;break;case 5:M64(0x39048)=0;break;case 6:G64(0x462e3d8)=0;break;case 7:G64(0x4900000)=0;break;case 8:G64(0x462e180)=0;break;case 9:G64(0x4901000)=0;break;}
  assert(!execute(0,index)&&!sets&&!offs);cases++;
 }
 // Exercise original begin/update/commit/close bytes with fake input and engine objects.
 void(*begin)(void*)=(void*)(mod+0x8280);void(*update)(void*)=(void*)(mod+0x90e0);
 void(*commit)(void*)=(void*)(mod+0x7b80);void(*close_wheel)(int,int)=(void*)(mod+0x85d0);
 unsigned char*nodes=calloc(5,0x1000),*screen=calloc(1,0x400);void*as=(void*)0x44440000;
 *(U*)(nodes+8)=(U)(nodes+0x1000);*(U*)(nodes+0x1008)=(U)(nodes+0x2000);
 *(U*)(nodes+0x21f8)=(U)(nodes+0x3000);*(U*)(nodes+0x3228)=(U)(nodes+0x4000);*(U*)(nodes+0x43a8)=(U)as;
 fail=0;
 for(int slot=0;slot<8;slot++){
  reset();memset(mod+0x576a0,0,0x900);mod[0x576b0]=1;M64(0x57ec8)=(U)as;
  M64(0x46678)=(U)query;M64(0x46598)=(U)original_update;
  M64(0x405b8)=(U)(mod+0x39080);M64(0x39080)=2;
  for(int j=0;j<8;j++)M32(0x23070+j*4)=j;
  M32(0x3d6f8)=-1;expected=map[slot];on=0;buttons=1UL<<15;ticks=100;
  begin(nodes);assert(M32(0x57f58)==1);update(nodes);assert(M32(0x57f58)==1&&!sets);
  ticks+=9599999;update(nodes);assert(M32(0x57f58)==1&&!sets);
  ticks++;update(nodes);assert(M32(0x57f58)==2&&!sets);
  // Native UI creation is mocked; commit and teardown logic execute unchanged.
  M32(0x57f58)=3;M64(0x576a0)=(U)screen;*(W*)(screen+0x23c)=slot;commit(screen);
  assert(M32(0x23090)==slot&&M32(0x57f50)==slot);
  buttons=0;close_wheel(0,1);assert(M32(0x57f58)==4&&M32(0x3d6f0)==slot);
  update(nodes);assert(M32(0x57f58)==0&&nodes[0x20]==1&&M32(0x3d6f8)==slot&&sets==(expected>=0));
  int previous=sets;update(nodes);assert(sets==previous);
  // A short new press/release must replay precisely that remembered definition.
  phase=sets=offs=0;on=1;buttons=1UL<<15;ticks+=100;begin(nodes);update(nodes);
  assert(M32(0x57f58)==1&&!sets);buttons=0;ticks+=100;update(nodes);
  assert(M32(0x57f58)==0&&sets==(expected>=0)&&offs==(expected>=0));
  previous=sets;update(nodes);assert(sets==previous);
  // Cancel a different highlighted slot; previous remembered selection survives.
  phase=sets=offs=0;M32(0x57f58)=3;M64(0x576a0)=(U)screen;M32(0x57f50)=(slot+1)%8;
  close_wheel(1,1);update(nodes);assert(!sets&&!offs&&M32(0x57f58)==0&&M32(0x3d6f8)==slot);
 }
 puts("PASS donor 500ms hold boundary, commit/release action, remembered tap action, exactly-once completion, and cancellation for eight slots (mock engine/UI creation).");
 printf("PASS %d executions of exact D08 AArch64 action bytes with mocked native services: mappings, reordered definitions, duplicate slots, ON/OFF order, lookup failures, null pointers, donor validation and return.\n",cases);

 // D11 native whistle handoff runs on the live native whistle node, never a rider node.
 void(*hb)(void*)=(void*)(mod+0x8184);void(*hu)(void*)=(void*)(mod+0x1be44);
 reset();memset(mod+0x576a0,0,0x900);memset(mod+0x59000,0,0x40);mod[0x576b0]=1;
 M64(0x57ec8)=(U)as;M64(0x46678)=(U)query;M64(0x465a0)=(U)horse_native_begin;M64(0x46598)=(U)horse_native_update;
 for(int j=0;j<8;j++)M32(0x23070+j*4)=j;
 M32(0x23090)=5;M32(0x3d6f8)=5;buttons=1UL<<15;ticks=100;nodes[0x20]=0;
 hb(nodes);hu(nodes);assert(M32(0x57f58)==1&&!horse_begins);
 buttons=0;hu(nodes);assert(horse_begins==1&&M64(0x59020)==(U)nodes&&!nodes[0x20]);
 hu(nodes);assert(horse_updates==1&&nodes[0x20]==1&&!M64(0x59020));
 assert(!sets&&!offs);puts("PASS Horse handoff: native begin once, native update owns completion, no Sage toggle or fabricated node.");
 // A subsequent selector gesture resets whistle ownership and still selects Tulin.
 horse_begins=horse_updates=0;M32(0x3d6f8)=0;M32(0x23090)=0;expected=0;phase=sets=offs=0;on=0;
 buttons=1UL<<15;ticks+=100;hb(nodes);hu(nodes);buttons=0;hu(nodes);assert(sets==1&&!horse_begins&&!horse_updates);
 // Mounted utility dispatch must never launch the on-foot whistle animation on Mineru.
 M64(0x59008)=(U)nodes;M32(0x59028)=0;M32(0x23090)=5;execute(as,5);assert(!M32(0x59028));
 puts("PASS selector after whistle, mounted rider exclusion, and unchanged Sage dispatcher.");
}
