typedef unsigned long U; extern char __module_start[]; U base(void){return (U)__module_start;} void foo(void){ *(volatile unsigned*)(base()+0x58000)=1; }
