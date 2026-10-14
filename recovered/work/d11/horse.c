typedef unsigned long U; typedef unsigned W;
extern char __module_start[];
#define P(a) (__module_start+(a))
#define V(t,a) (*(volatile t*)P(a))
#define FN(t,a) ((t)(U)V(U,a))
#define SEC(n) __attribute__((section(n),noinline))
extern void donor_begin(void*);extern void donor_update(void*);
#define ACTIVE V(U,0x59020)
#define REQUEST V(W,0x59028)
// Utility selection is synchronous; the live native whistle node owns playback.
SEC(".utility") void utility(void*as,unsigned slot){if(slot==5&&!V(U,0x59008))REQUEST=1;}
SEC(".horse_begin") void horse_begin(void*n){ACTIVE=0;REQUEST=0;donor_begin(n);}
SEC(".horse_update") void horse_update(void*n){
 if(ACTIVE==(U)n){FN(void(*)(void*),0x46598)(n);if(*((unsigned char*)n+0x20))ACTIVE=0;return;}
 REQUEST=0;donor_update(n);
 if(REQUEST){REQUEST=0;ACTIVE=(U)n;*((unsigned char*)n+0x20)=0;V(unsigned char,0x57f38)=0;FN(void(*)(void*),0x465a0)(n);}
}
