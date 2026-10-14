#pragma once
#include <cstdint>
#include <cstring>

namespace TotK::Emotes::ConfigFile {
constexpr int MaxEmotes = 64;
struct Emote {
    char id[64]{};
    char asCommand[128]{};
    char slink[128]{};
    char bntx[128]{}; // Reserved for custom UI textures; current sage icons are placeholders.
    char name[128]{};
    char16_t label[128]{};
    bool loop = false;
    uint32_t durationMs = 3000;
    uint32_t musicDelayMs = 0;
};
struct Config {
    Emote emotes[MaxEmotes]{};
    int count = 0;
    int lastEmote = -1;
    int slots[8] = {-1,-1,-1,-1,-1,-1,-1,-1};
};
inline constexpr const char* Positions[8] = {
    "Top", "Top Right", "Right", "Down Right", "Down", "Down Left", "Left", "Top Left"
};
// Small, bounded parser for the two configuration schemas. No heap allocations.
class Json {
    const char* p;
    static int Hex(char c) {
        if (c >= '0' && c <= '9') return c-'0';
        if (c >= 'a' && c <= 'f') return c-'a'+10;
        if (c >= 'A' && c <= 'F') return c-'A'+10;
        return -1;
    }
    bool Hex4(uint32_t& u) {
        u=0;
        for(int i=0;i<4;++i) {int h=Hex(*p);if(h<0){ return false; }++p;u=(u<<4)|h;}
        return true;
    }
public:
    explicit Json(const char* text):p(text) {
        if(static_cast<unsigned char>(p[0])==0xef && static_cast<unsigned char>(p[1])==0xbb && static_cast<unsigned char>(p[2])==0xbf) p+=3;
    }
    void Space() {while(*p==' '||*p=='\t'||*p=='\r'||*p=='\n')++p;}
    bool Take(char c) {Space();if(*p!=c){ return false; }++p;return true;}
    bool End() {Space();return *p==0;}
    const char* Cursor() const {return p;}
    bool Word(const char* s) {Space();size_t n=std::strlen(s);if(std::strncmp(p,s,n)){ return false; }p+=n;return true;}
    bool String(char* out,size_t capacity) {
        if(!Take('"')){ return false; }
        size_t n=0;
        auto put=[&](unsigned char c){if(n+1>=capacity||c==0){ return false; }out[n++]=char(c);return true;};
        while(*p && *p!='"') {
            unsigned char c=*p++;
            if(c<0x20){ return false; }
            if(c!='\\') {if(!put(c)){ return false; }continue;}
            c=*p;if(!c){ return false; }++p;
            if(c=='"'||c=='\\'||c=='/') {if(!put(c)){ return false; }}
            else if(c=='n'||c=='r'||c=='t'||c=='b'||c=='f') {
                char v=c=='n'?'\n':c=='r'?'\r':c=='t'?'\t':c=='b'?'\b':'\f';if(!put(v)){ return false; }
            } else if(c=='u') {
                uint32_t u;if(!Hex4(u)){ return false; }
                if(u>=0xd800&&u<=0xdbff) {
                    if(p[0]!='\\'||p[1]!='u'){ return false; }p+=2;
                    uint32_t low;if(!Hex4(low)||low<0xdc00||low>0xdfff){ return false; }
                    u=0x10000+((u-0xd800)<<10)+(low-0xdc00);
                } else if(u>=0xdc00&&u<=0xdfff){ return false; }
                if(u<0x80) {if(!put(u)){ return false; }}
                else if(u<0x800) {if(!put(0xc0|(u>>6))||!put(0x80|(u&63))){ return false; }}
                else if(u<0x10000) {if(!put(0xe0|(u>>12))||!put(0x80|((u>>6)&63))||!put(0x80|(u&63))){ return false; }}
                else if(!put(0xf0|(u>>18))||!put(0x80|((u>>12)&63))||!put(0x80|((u>>6)&63))||!put(0x80|(u&63))){ return false; }
            } else { return false; }
        }
        if(*p!='"'){ return false; }++p;out[n]=0;return true;
    }
    bool Bool(bool& v) {if(Word("true")){v=true;return true;}if(Word("false")){v=false;return true;}{ return false; }}
    bool UInt(uint32_t& v) {
        Space();if(*p<'0'||*p>'9'){ return false; }
        v=0;bool zero=*p=='0';int digits=0;
        do {if(v>360000){ return false; }v=v*10+(*p++-'0');++digits;}while(*p>='0'&&*p<='9');
        return !(zero&&digits>1) && v<=3600000;
    }
};
inline bool ToUtf16(const char* src,char16_t* dst,size_t cap) {
    size_t n=0;const auto* p=reinterpret_cast<const unsigned char*>(src);
    while(*p) {
        uint32_t u=*p++;int extra=0;uint32_t min=0;
        if(u>=0xf0&&u<=0xf4){extra=3;u&=7;min=0x10000;}
        else if(u>=0xe0&&u<=0xef){extra=2;u&=15;min=0x800;}
        else if(u>=0xc2&&u<=0xdf){extra=1;u&=31;min=0x80;}
        else if(u>=0x80){ return false; }
        for(int i=0;i<extra;++i){if((*p&0xc0)!=0x80){ return false; }u=(u<<6)|(*p++&63);}
        if(u<min||u>0x10ffff||(u>=0xd800&&u<=0xdfff)){ return false; }
        if(u>=0x10000){if(n+2>=cap){ return false; }u-=0x10000;dst[n++]=0xd800+(u>>10);dst[n++]=0xdc00+(u&1023);}
        else {if(n+1>=cap){ return false; }dst[n++]=char16_t(u);}
    }
    dst[n]=0;return true;
}
inline int Find(const Config& c,const char* id) {
    for(int i=0;i<c.count;++i)if(!std::strcmp(c.emotes[i].id,id))return i;
    return -1;
}
inline bool CleanName(const char* s,bool empty=false) {
    if(!empty&&!*s){ return false; }
    for(;*s;++s)if(static_cast<unsigned char>(*s)<0x20){ return false; }
    return true;
}
// The last-used ID is optional, so old wheel files remain valid. An ID removed
// from the library simply means there is no repeat target after restart.
inline bool ParseWheel(const char* text,const Config& c,int* slots,int& last,
                       const char** valueBegin=nullptr,const char** valueEnd=nullptr,
                       const char** rootEnd=nullptr) {
    for(int i=0;i<8;++i) slots[i]=-1;
    last=-1;Json w(text);char key[64];unsigned fields=0;
    if(valueBegin)*valueBegin=nullptr;
    if(valueEnd)*valueEnd=nullptr;
    if(!w.Take('{')||w.Take('}')) return false;
    do {
        if(!w.String(key,sizeof(key))||!w.Take(':'))return false;
        if(!std::strcmp(key,"slots")) {
            if(fields&1)return false;
            fields|=1;
            if(!w.Take('{'))return false;
            unsigned seen=0;
            if(!w.Take('}')) {
                do {
                    if(!w.String(key,sizeof(key))||!w.Take(':'))return false;
                    int slot=-1;for(int i=0;i<8;++i)if(!std::strcmp(key,Positions[i]))slot=i;
                    if(slot<0||(seen&(1u<<slot)))return false;
                    seen|=1u<<slot;
                    if(w.Word("null"))slots[slot]=-1;
                    else {if(!w.String(key,sizeof(key)))return false;slots[slot]=Find(c,key);if(slots[slot]<0)return false;}
                }while(w.Take(','));
                if(!w.Take('}'))return false;
            }
        } else if(!std::strcmp(key,"_note")) {
            if(fields&4)return false;
            fields|=4;
            char note[512];
            if(!w.String(note,sizeof(note))||!CleanName(note))return false;
        } else if(!std::strcmp(key,"lastEmoteUsed")) {
            if(fields&2)return false;
            fields|=2;
            w.Space();if(valueBegin)*valueBegin=w.Cursor();
            if(!w.Take('{')||!w.String(key,sizeof(key))||std::strcmp(key,"id")||!w.Take(':'))return false;
            if(!w.Word("null")) {
                if(!w.String(key,sizeof(key))||!CleanName(key))return false;
                char16_t valid[64];if(!ToUtf16(key,valid,64))return false;
                last=Find(c,key);
            }
            if(!w.Take('}'))return false;
            if(valueEnd)*valueEnd=w.Cursor();
        } else return false;
    }while(w.Take(','));
    w.Space();if(rootEnd)*rootEnd=w.Cursor();
    return (fields&1)&&w.Take('}')&&w.End();
}

// Separate writable state: independent of wheel assignments and library ordering.
inline bool ParseLastUsed(const char* text,const Config& c,int& last) {
    Json j(text);char key[64],id[64];int resolved=-1;
    if(!j.Take('{')||!j.String(key,sizeof(key))||std::strcmp(key,"lastEmoteUsed")||
       !j.Take(':')||!j.Take('{')||!j.String(key,sizeof(key))||std::strcmp(key,"id")||!j.Take(':'))return false;
    if(!j.Word("null")) {
        if(!j.String(id,sizeof(id))||!CleanName(id))return false;
        char16_t valid[64];if(!ToUtf16(id,valid,64))return false;
        resolved=Find(c,id);
    }
    if(!j.Take('}')||!j.Take('}')||!j.End())return false;
    last=resolved;return true;
}
inline bool WriteLastUsed(const Config& c,const char* id,char* out,size_t cap) {
    if(id&&(Find(c,id)<0||!CleanName(id)))return false;
    size_t n=0;
    auto put=[&](char ch){if(n+1>=cap)return false;out[n++]=ch;return true;};
    for(const char* p="{\n  \"lastEmoteUsed\": {\"id\": ";*p;++p)if(!put(*p))return false;
    if(id) {
        if(!put('"'))return false;
        for(const char* p=id;*p;++p){if((*p=='"'||*p=='\\')&&!put('\\'))return false;if(!put(*p))return false;}
        if(!put('"'))return false;
    } else for(const char* p="null";*p;++p)if(!put(*p))return false;
    for(const char* p="}\n}\n";*p;++p)if(!put(*p))return false;
    out[n]=0;return true;
}

// Patch only the last-used section, preserving the user's slots and formatting.
inline bool UpdateLastUsed(const char* wheel,const Config& c,const char* id,char* out,size_t cap) {
    int slots[8],last;const char *begin,*end,*root;
    if(Find(c,id)<0||!ParseWheel(wheel,c,slots,last,&begin,&end,&root))return false;
    char section[160];size_t n=0;
    auto put=[&](char ch){if(n+1>=sizeof(section))return false;section[n++]=ch;return true;};
    for(const char* p="{\"id\": \"";*p;++p)if(!put(*p))return false;
    for(const char* p=id;*p;++p){if((*p=='"'||*p=='\\')&&!put('\\'))return false;if(!put(*p))return false;}
    for(const char* p="\"}";*p;++p)if(!put(*p))return false;
    section[n]=0;
    const char* insert=begin?begin:root;const char* tail=begin?end:root;
    const char* prefix=begin?"":",\n  \"lastEmoteUsed\": ";
    size_t a=size_t(insert-wheel),b=std::strlen(prefix),d=std::strlen(tail);
    if(a+b+n+d>=cap)return false;
    std::memcpy(out,wheel,a);std::memcpy(out+a,prefix,b);std::memcpy(out+a+b,section,n);std::memcpy(out+a+b+n,tail,d+1);
    return true;
}

inline bool Parse(const char* library,const char* wheel,Config& c) {
    c=Config{};Json j(library);char key[64];
    if(!j.Take('{')||!j.String(key,sizeof(key))||std::strcmp(key,"emotes")||!j.Take(':')||!j.Take('{')){ return false; }
    if(!j.Take('}'))do {
        if(c.count>=MaxEmotes){ return false; }
        auto& e=c.emotes[c.count];
        if(!j.String(e.id,sizeof(e.id))||!CleanName(e.id)||Find(c,e.id)>=0||!j.Take(':')||!j.Take('{')){ return false; }
        unsigned seen=0;
        if(j.Take('}')){ return false; }
        do {
            if(!j.String(key,sizeof(key))||!j.Take(':')){ return false; }
            int field=-1;
            const char* names[]={"ASCommand","SLink","Bntx","Name","Loop","DurationMs","MusicDelayMs","EmoteID"};
            for(int i=0;i<8;++i)if(!std::strcmp(key,names[i]))field=i;
            if(field<0||(seen&(1u<<field))){ return false; }seen|=1u<<field;
            bool ok=false;
            switch(field) {
                case 0:ok=j.String(e.asCommand,sizeof(e.asCommand))&&CleanName(e.asCommand);break;
                case 1:ok=j.String(e.slink,sizeof(e.slink))&&CleanName(e.slink,true);break;
                case 2:ok=j.String(e.bntx,sizeof(e.bntx))&&CleanName(e.bntx,true);break;
                case 3:ok=j.String(e.name,sizeof(e.name))&&CleanName(e.name);break;
                case 4:ok=j.Bool(e.loop);break;
                case 5:ok=j.UInt(e.durationMs)&&e.durationMs>0;break;
                case 6:ok=j.UInt(e.musicDelayMs);break;
                case 7:{char id[64];ok=j.String(id,sizeof(id))&&!std::strcmp(id,e.id);break;}
            }
            if(!ok){ return false; }
        }while(j.Take(','));
        if(!j.Take('}')||(seen&7)!=7){ return false; }
        if(!(seen&8))std::strcpy(e.name,e.id);
        if(!ToUtf16(e.name,e.label,128)){ return false; }
        ++c.count;
    }while(j.Take(','));else goto library_closed;
    if(!j.Take('}')){ return false; }
library_closed:
    if(!j.Take('}')||!j.End()){ return false; }
    return ParseWheel(wheel,c,c.slots,c.lastEmote);
}
} // namespace TotK::Emotes::ConfigFile
