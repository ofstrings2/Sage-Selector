typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32; typedef unsigned long u64; typedef long i64;
extern char __module_start[];
static u64 self(void){return (u64)__module_start;}
#define AT(type,off) (*(volatile type*)(self()+(off)))
#define FN(type,off) ((type)(self()+(off)))
static u64 mainbase(void){return *(u64*)(AT(u64,0x40568)+0x48);}
#define GAME(type,off) ((type)(mainbase()+(off)))
struct State {u32 active,selected,ready,pad;u64 pressed,tick_original;u32 dispatches,last_error;};
#define S ((volatile struct State*)(self()+0x38000))
struct Hid {u64 sample,buttons;int lx,ly,rx,ry;u32 attr,pad;};
extern u64 donor_hook(u64,u64,int);extern void donor_open_step(void);extern void donor_close_body(int,int);extern void donor_cleanup(void);extern void donor_wheel_open(void*);extern void donor_wheel_update(void*);extern void factory0(void);extern void factory1(void);
static u64 ticks(void){u64 v;__asm__ volatile("mrs %0, cntpct_el0":"=r"(v));return v;}
static int hid(struct Hid* out){
 u32 ids[2]={0,0x20};
 for(int j=0;j<2;j++){u32 id=ids[j];u32 style=FN(u32(*)(u32*),0x1b990)(&id);
  for(int i=0;i<3;i++)if(style&(1u<<i)){
   struct Hid h={0};u64 off=i==0?0x1ba00:i==1?0x1b9d0:0x1b9b0;
   if(FN(int(*)(struct Hid*,int,u32*),off)(&h,1,&id)==1&&(h.attr&1)){*out=h;return 1;}
  }
 }return 0;
}
static void finish_node(void* p){u32 f=*(u32*)((u64)p+0x18);*(u32*)((u64)p+0x18)=(f&0x3fffffff)|0x80000000;}
void begin(void* p){
 struct Hid h={0};
 if(S->ready&&!S->active&&hid(&h)&&(h.buttons&(1u<<11))&&!(h.buttons&((1u<<1)|(1u<<6)|(1u<<10)))){
  S->active=1;S->pressed=ticks();AT(u32,0x57f58)=1;AT(u32,0x23090)=S->selected;
 }
 finish_node(p);
}
const char* node_name(void){return "SeqOneShotSageWheelBegin";}
void* construct(void* heap){
 u64 p=GAME(u64(*)(u32,void*,u32),0x7fa8f0)(0x190,heap,8);if(!p)return (void*)0;
 for(u32 i=0;i<0x60;i++)*(u8*)(p+i)=0;
 *(u16*)(p+0x1e)=255;
 for(u32 i=0;i<0x130;i+=8)*(u64*)(p+0x60+i)=*(u64*)(mainbase()+0x43aa1e0+i);
 *(u64*)p=p+0x70;*(u64*)(p+0x70+0x110)=(u64)begin;*(u64*)(p+0x70+0x88)=(u64)node_name;return (void*)p;
}
// Same hierarchy and native APIs used by 1.2.1's own companion setter.
static void dispatch(u32 slot){
 const int indices[8]={0,-1,1,4,2,-1,3,-1};if(slot>7||indices[slot]<0)return;
 u32 idx=(u32)indices[slot];u64 root=*(u64*)(mainbase()+0x462e3d8);if(!root){S->last_error=1;return;}u64 gd=*(u64*)root;if(!gd){S->last_error=2;return;}
 u64 handles[6]={0};u32 hashes[5]={0x8c63f616,0x4dd38161,0xd21b65b6,0x361877c4,0x15576a07};u8 on=0;
 if(!GAME(int(*)(u64,void*,u32),0xddbb04)(gd,handles,0x060890b0)||
 !GAME(int(*)(u64,void*,void*,u32),0x80e6c4)(gd,handles+2,handles,0x42026d93)||
 !GAME(int(*)(u64,void*,void*,u32),0x80e6c4)(gd,handles+4,handles+2,hashes[idx])||
 !GAME(int(*)(u64,u8*,void*,u32),0x92a3e4)(gd,&on,handles+4,0xe2d35fd8)){S->last_error=3;return;}
 u64 mgr=*(u64*)(mainbase()+0x462e180);if(!mgr||!*(u64*)mgr){S->last_error=4;return;}
 u64 sys=GAME(u64(*)(u64,u32),0xf68af0)(*(u64*)mgr,0x12);if(!sys){S->last_error=5;return;}
 GAME(void(*)(u64,u32,u32),0x196110c)(sys,idx,on?0:1);
 if(on)GAME(void(*)(u64,u32,u32),0x92a8cc)(sys,idx,1);
 S->dispatches++;S->last_error=0;
}
void close_wheel(int cancel,int after){
 if(AT(u8,0x57f28)){donor_close_body(cancel,after);return;}
 u32 hovered=AT(u32,0x57f50);int was_open=AT(u32,0x57f58)==3;
 donor_close_body(cancel,after);donor_cleanup();
 if(!cancel&&was_open&&hovered<8)S->selected=hovered;
 AT(u32,0x23090)=S->selected;AT(u32,0x3d6f0)=~0u;AT(u32,0x57f58)=0;S->active=0;
}
static void step(void){
 if(!S->active)return;struct Hid h={0};int ok=hid(&h);u32 st=AT(u32,0x57f58);
 if(!ok||(h.buttons&((1u<<1)|(1u<<6)|(1u<<10)))){close_wheel(1,0);return;}
 int held=(h.buttons&(1u<<11))!=0;
 if(st==1){
  if(!held){S->active=0;AT(u32,0x57f58)=0;dispatch(S->selected);return;}
  if(ticks()-S->pressed<4800000)return; // 250 ms, Switch 19.2 MHz system counter
  AT(u32,0x57f58)=2;st=2;
 }
 if(st==2&&!held){close_wheel(1,0);return;}
 if(st==2||st==3)donor_open_step();
}
void tick(void* framework){
 // Before the native frame: AINB begin authorizes only actual gameplay Minus presses.
 step();((void(*)(void*))S->tick_original)(framework);
}
// Explicit physical right-stick octants; 25% dead zone, 3 degree angular hysteresis.
static u32 octant(int x,int y,u32 old){
 i64 ax=x<0?-(i64)x:x,ay=y<0?-(i64)y:y;
 if(ax*ax+ay*ay<8192L*8192L)return old;
 const float vx[8]={0,.70710678f,1,.70710678f,0,-.70710678f,-1,-.70710678f};
 const float vy[8]={1,.70710678f,0,-.70710678f,-1,-.70710678f,0,.70710678f};
 if(old<8){float dot=x*vx[old]+y*vy[old];if(dot>0&&dot*dot>0.81466f*((float)x*x+(float)y*y))return old;}
 if(ax*100000<ay*41421)return y>0?0:4;
 if(ay*100000<ax*41421)return x>0?2:6;
 return y>0?(x>0?1:7):(x>0?3:5);
}
void wheel_update(void* ptr){
 u64 p=(u64)ptr;
 if(!p||AT(u64,0x576a0)!=p||AT(u32,0x57f58)!=3){((void(*)(void*))AT(u64,0x46578))(ptr);return;}
 struct Hid h={0};if(!hid(&h)||!(h.buttons&(1u<<11))||(h.buttons&2)){close_wheel((h.buttons&2)!=0,0);return;}
 u32 old=AT(u32,0x57f50),sel=octant(h.rx,h.ry,old);if(sel>7)sel=S->selected;
 ((void(*)(void*))AT(u64,0x46578))(ptr);
 // Replace only this active Sage session's selection and highlight.
 u32 native_sel=*(u32*)(p+0x23c);*(u32*)(p+0x23c)=sel;*(u32*)(p+0x240)=sel;*(u8*)(p+0x245)=1;AT(u32,0x57f50)=sel;
 u64 panes=*(u64*)(p+0x1b0);u32 count=*(u32*)(p+0x1a8);
 if(panes&&(old!=sel||native_sel!=sel))for(u32 i=0;i<8&&i<count;i++){u64 pane=*(u64*)(panes+i*8);if(!pane)continue;
  ((void(*)(u64,int))AT(u64,0x46618))(pane,i==sel);
  ((void(*)(u64,u64))AT(u64,i==sel?0x46610:0x46608))(pane,1);
 }
 u64 layout=*(u64*)(p+0x28);if(layout){u64 text=((u64(*)(u64,const char*))AT(u64,0x46628))(layout,"T_Text_00");
  if(text){u16* label=(u16*)(self()+0x303c8+sel*0x34c+0x240);u32 n=0;while(label[n])n++;((void(*)(u64,u16*,u64,u32))AT(u64,0x46620))(text,label,0,n);}}
}
static void copy8(char* d,const char*s){while((*d++=*s++));}
static void copy16(u16*d,const char*s){while((*d++=(u8)*s++));}
void init(void){
 S->ready=0;S->active=0;S->selected=0;S->dispatches=0;S->last_error=0;
 u64 b=mainbase();AT(u64,0x38030)=b;
 // Fail closed against the exact clean 1.2.1 instructions before any game patches.
 if(*(u32*)(b+0x77a100)!=0x14000005||*(u32*)(b+0x77a3cc)!=0x14000005||*(u32*)(b+0x9d1d30)!=0xa9be7bfd)return;
 i64 d0=(i64)(u64)factory0-(i64)(b+0x77a100),d1=(i64)(u64)factory1-(i64)(b+0x77a3cc);
 if(d0<=-0x7fffff8||d0>=0x7fffff8||d1<=-0x7fffff8||d1>=0x7fffff8)return;
 const u32 offsets[][2]={{0x668,0x19ad66c},{0x670,0x19a3610},{0x660,0x2a69044},{0x658,0x19ad6d4},{0x650,0x19b8df0},{0x648,0x2a6908c},{0x640,0x1b1e4f8},{0x638,0x1b1e514},{0x630,0x19ad3f4},{0x628,0x7012ec},{0x620,0xc74cb4},{0x618,0x1b1e534},{0x610,0x1acc214},{0x608,0x1acc2b8},{0x600,0x1acc35c},{0x5f8,0x89011c},{0x5e8,0x102361c},{0x5e0,0xf48498}};
 for(u32 i=0;i<sizeof(offsets)/sizeof(offsets[0]);i++)AT(u64,0x46000+offsets[i][0])=b+offsets[i][1];
 const char names[8][8]={"Tulin","Memory","Yunobo","Mineru","Sidon","Horse","Riju","Warp"};
 const char icons[8][32]={"Obj_SageSoul_Rito","Obj_Camera","Obj_SageSoul_Goron","Obj_SageSoul_Zonau","Obj_SageSoul_Zora","GameRomHorseSaddle_00","Obj_SageSoul_Gerudo","Obj_Warp"};
 for(u32 i=0;i<8;i++){u64 p=self()+0x303c8+i*0x34c;for(u32 j=0;j<0x34c;j++)*(u8*)(p+j)=0;copy8((char*)p,names[i]);copy8((char*)(p+0x140),icons[i]);copy16((u16*)(p+0x240),names[i]);AT(u32,0x23070+i*4)=i;}
 AT(u32,0x3d6c8)=8;AT(u32,0x23090)=0;AT(u32,0x3d6f0)=~0u;AT(u32,0x57f58)=0;
 const u32 hooks[][3]={{0x1b1dc94,0x9760,0x580},{0x1b1eef8,0x7b80,0x570},{0x1b1eeb8,0x8e30,0x568},{0xd17e60,0x7a70,0x5b0}};
 for(u32 i=0;i<sizeof(hooks)/sizeof(hooks[0]);i++)AT(u64,0x46000+hooks[i][2])=donor_hook(b+hooks[i][0],self()+hooks[i][1],1);
 AT(u64,0x46578)=donor_hook(b+0x1b1e65c,(u64)wheel_update,1);
 S->tick_original=donor_hook(b+0x9d1d30,(u64)tick,1);
 donor_hook(b+0x77a100,(u64)factory0,0);donor_hook(b+0x77a3cc,(u64)factory1,0);
 S->ready=1;
}
