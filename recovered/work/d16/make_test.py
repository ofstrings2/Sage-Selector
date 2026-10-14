from pathlib import Path
s=Path('work/d15/regression.c').read_text()
s=s.replace('static int evphase,accepted=1;', 'static int sleep_calls;static void sleep_spy(void*a){sleep_calls++;}\nstatic int evphase,accepted=1;')
s=s.replace('modstub(0x81d4,log_mock);','modstub(0x81d4,sleep_spy);')
pos=s.rfind('}')
s=s[:pos]+'''
 // Reproduce a lost mounted-end callback by preserving its process-local NODE.
 // Then enter an authentic on-foot Whistle callback with a NEW AS context.
 for(int gesture=0;gesture<2;gesture++)for(int slot=0;slot<8;slot++){
  reset();fail=0;on=0;expected=map[slot];evphase=horse_begins=horse_updates=sleep_calls=0;
  memset(mod+0x576a0,0,0x900);memset(mod+0x59000,0,0x50);mod[0x576b0]=1;
  void*fresh_as=(void*)(0x55550000UL+0x100UL*slot+0x1000UL*gesture);
  *(U*)(nodes+0x43a8)=(U)fresh_as;M64(0x57ec8)=0x11111111;
  M64(0x59008)=0xdead0000; // lost end callback; never dereference this pointer
  M64(0x46678)=(U)query;M64(0x465a0)=(U)horse_native_begin;M64(0x46598)=(U)horse_native_update;
  M64(0x405b8)=(U)(mod+0x39080);M64(0x39080)=2;
  G64(0x462e3e8)=(U)(game+0x4902000);G64(0x4902000)=0x12340000;
  for(int j=0;j<8;j++)M32(0x23070+j*4)=j;
  M32(0x23090)=slot;M32(0x3d6f8)=slot;buttons=1UL<<15;ticks=100;accepted=1;
  hb(nodes);hu(nodes);assert(M64(0x57ec8)==(U)fresh_as);
  if(gesture){ticks+=9600000;hu(nodes);assert(M32(0x57f58)==2);M32(0x57f58)=3;M64(0x576a0)=(U)screen;*(W*)(screen+0x23c)=slot;commit(screen);buttons=0;close_wheel(0,1);}
  buttons=0;hu(nodes);
  int want_fixed=EXPECTED_FIXED;
  assert(sets==(expected>=0));
  assert(horse_begins==(slot==5&&want_fixed));
  assert(evphase==(slot==1&&want_fixed?5:0));
  assert(sleep_calls==(slot==7));
  assert(M32(0x57f58)==0&&M32(0x3d6f8)==slot);
  printf("INJECTED stale NODE / %s / slot %d: sage=%d horse=%d memory=%d sleep_dispatch=%d fresh_context=yes\\n",gesture?"hold/select/release":"tap",slot,sets,horse_begins,evphase==5,sleep_calls);
 }
''' +s[pos:]
Path('work/d16/repro_template.c').write_text(s)
Path('work/d16/repro_d15.c').write_text(s.replace('EXPECTED_FIXED','0'))
