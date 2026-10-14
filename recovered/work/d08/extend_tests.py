from pathlib import Path
s=Path('work/d08/test_payload.c').read_text()
p=s.index('int main(void)')
s=s[:p]+'''static U buttons,ticks;static int original_calls;
static int query(void*a,W id){return id==0x12&&((buttons>>15)&1);}
static int hid(U*out){*out=buttons;return 1;}
static U clock_mock(void){return ticks;}
static void log_mock(void){}
static void original_update(unsigned char*n){original_calls++;n[0x20]=1;}
static void modstub(U at,void*p){W code[]={0x58000050,0xd61f0200};memcpy(mod+at,code,8);memcpy(mod+at+8,&p,8);}
'''+s[p:]
s=s.replace('__builtin___clear_cache((char*)mod', 'modstub(0x7910,hid);modstub(0xd614,clock_mock);modstub(0x7690,log_mock);\n __builtin___clear_cache((char*)mod',1)
p=s.index('printf("PASS %d executions')
s=s[:p]+'''// Exercise original begin/update/commit/close bytes with fake input and engine objects.
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
 '''+s[p:]
Path('work/d08/test_integration.c').write_text(s)
