from pathlib import Path
s=Path('work/d11/test_integration.c').read_text().replace('work/d11/d11.bin','work/d12/d12.bin').replace('work/d11/build/Sage Selector D11','work/d12/build/Sage Selector D12')
mocks='''
static int evphase,accepted=1;static unsigned char*evarg;
static void evctor(unsigned char*a){assert(evphase++==0&&!((U)a&15));evarg=a;memset(a,0,0x1b20);}
static void evname(unsigned char*a,const char**n,int len){assert(evphase++==1&&a==evarg+0x1a90&&len==-1);assert(!strcmp(*n,"DmT_OP_GanonWakeUp_PreRender_Memory"));}
static int evrequest(U manager,unsigned char*a){assert(evphase++==2&&manager==0x12340000&&a==evarg);return accepted;}
static void evdestroy(unsigned char*a){assert(a==evarg+(evphase==3?0x1968:0x1950));evphase++;}
'''
s=s.replace('int main(void){',mocks+'\nint main(void){')
s=s.replace('0x92a8cc};void* fs[]={root,child,boolean,system_get,set,off};','0x92a8cc,0x10229b0,0xb51c14,0x11f0700,0x76eb88};void* fs[]={root,child,boolean,system_get,set,off,evctor,evname,evrequest,evdestroy};').replace('i<6;i++','i<10;i++')
extra='''
 M64(0x59008)=0;reset();M32(0x23090)=1;evphase=0;G64(0x462e3e8)=(U)(game+0x4902000);G64(0x4902000)=0x12340000;
 for(accepted=0;accepted<2;accepted++){evphase=0;execute(as,1);assert(evphase==5&&!sets&&!offs&&M32(0x3d6f8)==1);}
 evphase=0;M64(0x59008)=(U)nodes;execute(as,1);assert(!evphase);M64(0x59008)=0;
 G64(0x4902000)=0;execute(as,1);assert(!evphase);G64(0x462e3e8)=0;execute(as,1);assert(!evphase);
 puts("PASS Memory exact AArch64 ABI: aligned request, correct event, request once, both native destructors on acceptance/rejection; mounted/null guards.");
'''
s=s[:s.rfind('}')]+extra+'}\n';Path('work/d12/test.c').write_text(s)
