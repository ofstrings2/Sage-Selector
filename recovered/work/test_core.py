exec(open('work/decode_donors.py').read().split('D=Path')[0])
import unicorn as u
from unicorn.arm64_const import *
import math
syms=json.loads(Path('work/core.symbols.json').read_text());E=0x16000000;G=0x10000000;STACK=0x30000000;STOP=0x30010000
uc=u.Uc(u.UC_ARCH_ARM64,u.UC_MODE_ARM);uc.mem_map(G,0x5000000);uc.mem_map(E,0x60000);uc.mem_map(STACK,0x20000);uc.mem_write(E,Path('work/sage.memory.bin').read_bytes())
def put(a,v,n=8):uc.mem_write(a,int(v).to_bytes(n,'little'))
def get(a,n=8):return int.from_bytes(uc.mem_read(a,n),'little')
put(E+0x40568,E+0x39000);put(E+0x39048,G);put(E+0x38030,G)
put(G+0x462e3d8,G+0x4900000);put(G+0x4900000,G+0x4900100);put(G+0x462e180,G+0x4901000);put(G+0x4901000,G+0x4901100)
put(E+0x38004,0,4);put(E+0x38008,1,4);put(E+0x38018,STOP)
now=0;buttons=0;stick=(0,0);on=0;calls=[];opened=0
xregs=[UC_ARM64_REG_X0+i for i in range(29)]+[UC_ARM64_REG_X29,UC_ARM64_REG_X30]
md=capstone.Cs(capstone.CS_ARCH_ARM64,capstone.CS_MODE_ARM)
cp={}
for ins in md.disasm(Path('work/core.bin').read_bytes()[:3196],0xa000):
 if ins.mnemonic=='mrs' and 'cntpct_el0' in ins.op_str:cp[E+ins.address]=int(ins.op_str.split(',')[0][1:])
def ret(value=0):uc.reg_write(UC_ARM64_REG_X0,value);uc.reg_write(UC_ARM64_REG_PC,uc.reg_read(UC_ARM64_REG_LR))
def hook(uc,addr,size,data):
 global opened
 if addr in cp:uc.reg_write(xregs[cp[addr]],now);uc.reg_write(UC_ARM64_REG_PC,addr+4);return
 a=[uc.reg_read(xregs[i]) for i in range(5)]
 if addr==E+0x1b990:ret(1)
 elif addr in [E+0x1ba00,E+0x1b9d0,E+0x1b9b0]:
  uc.mem_write(a[0],struct.pack('<QQiiiiII',1,buttons,0,0,*stick,1,0));ret(1)
 elif addr in [G+0xddbb04,G+0x80e6c4]:put(a[1],G+0x4910000);ret(1)
 elif addr==G+0x92a3e4:put(a[1],on,1);ret(1)
 elif addr==G+0xf68af0:ret(G+0x4920000)
 elif addr in [G+0x196110c,G+0x92a8cc]:calls.append((hex(addr-G),a[1],a[2]));ret()
 elif addr==E+0x8810:opened+=1;put(E+0x57f58,3,4);ret()
 elif addr==E+0x7770:put(E+0x57f58,4,4);ret()
 elif addr==E+0x8050:ret()
 elif addr==G+0x7fa8f0:ret(G+0x4930000)
 elif addr==STOP:uc.emu_stop()
uc.hook_add(u.UC_HOOK_CODE,hook)
def run(name,*args):
 uc.reg_write(UC_ARM64_REG_SP,STACK+0x8000);uc.reg_write(UC_ARM64_REG_LR,STOP)
 for i,a in enumerate(args):uc.reg_write(xregs[i],a)
 print('RUN',name,hex(E+syms[name]),flush=True)
 uc.emu_start(E+syms[name],STOP+4,count=100000)
 assert uc.reg_read(UC_ARM64_REG_PC)==STOP,(name,hex(uc.reg_read(UC_ARM64_REG_PC)))
checks=[]
node=G+0x4940000
for slot,index in [(0,0),(2,1),(3,4),(4,2),(6,3)]:
 for on in [0,1]:
  calls.clear();put(E+0x38004,slot,4);buttons=1<<11;now+=10000000;run('begin',node);assert get(E+0x38000,4)==1
  buttons=0;now+=1000000;run('tick',0)
  assert calls==[('0x196110c',index,1)] if not on else calls==[('0x196110c',index,0),('0x92a8cc',index,1)],calls
  run('tick',0);assert len(calls)==1+on
checks.append('Five sage indices, both directions: exactly-once native setter; native dismissal follows only OFF')
for slot in [1,5,7]:
 put(E+0x38004,slot,4);calls.clear();buttons=1<<11;now+=10000000;run('begin',node);buttons=0;run('tick',0);assert not calls
checks.append('Three utility slots inert')
put(E+0x38004,6,4);buttons=1<<11;now+=10000000;calls.clear();run('begin',node);now+=4799999;run('tick',0);assert get(E+0x57f58,4)==1 and not calls
now+=1;run('tick',0);assert get(E+0x57f58,4)==3 and not calls
put(E+0x57f50,3,4);run('close_wheel',0,0);assert get(E+0x38004,4)==3 and get(E+0x57f58,4)==0 and not calls
buttons=0;run('tick',0);assert not calls
checks.append('250ms hold opens without action; selection release commits without action; selection persists')
buttons=1<<11;now+=10000000;run('begin',node);put(E+0x57f58,3,4);put(E+0x57f50,7,4);run('close_wheel',1,0);assert get(E+0x38004,4)==3
checks.append('Cancellation preserves selection')
for mask in [0,1<<6,1<<10,1<<15,(1<<11)|(1<<10)]:
 buttons=mask;run('begin',node);assert get(E+0x38000,4)==0
checks.append('No arm from Map-style no physical Minus, L, Plus or Down; simultaneous Minus+Plus rejected')
run('construct',G+0x4950000);p=uc.reg_read(UC_ARM64_REG_X0);assert p==G+0x4930000;assert get(p+0x1e,2)==255;assert get(p)==p+0x70;assert get(p+0x180)==E+syms['begin']
checks.append('Custom AINB object constructor header and private vtable match donor contract')
Path('work/core_tests.json').write_text(json.dumps({'checks':checks,'runtime_game_tested':False,'method':'Unicorn executes compiled AArch64 core with mocked Nintendo HID and native game calls'},indent=2));print('\n'.join(checks))
