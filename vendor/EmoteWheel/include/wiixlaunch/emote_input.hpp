#pragma once
#include <cstdint>
#include <cstddef>

// Public SDK exports verified in this game's sdk NSO. Npad IDs are const u32&.
// The SDK copies 0x28 bytes per state; sampling number at +0, buttons at +8.
namespace nn::hid {
#define EMOTE_NPAD_STATE(Name) struct Name { \
    int64_t samplingNumber; uint64_t buttons; \
    int32_t leftX,leftY,rightX,rightY; uint32_t attributes,reserved; };
EMOTE_NPAD_STATE(NpadFullKeyState)
EMOTE_NPAD_STATE(NpadHandheldState)
EMOTE_NPAD_STATE(NpadJoyDualState)
#undef EMOTE_NPAD_STATE
// Native BitFlagSet<32> is returned in w0; the public function's name has no
// return-type component. This declaration preserves that four-byte ABI.
uint32_t GetNpadStyleSet(const uint32_t& id);
int GetNpadStates(NpadFullKeyState*,int,const uint32_t&);
int GetNpadStates(NpadHandheldState*,int,const uint32_t&);
int GetNpadStates(NpadJoyDualState*,int,const uint32_t&);
static_assert(sizeof(NpadFullKeyState)==0x28);
static_assert(sizeof(NpadHandheldState)==0x28);
static_assert(sizeof(NpadJoyDualState)==0x28);
static_assert(offsetof(NpadFullKeyState,buttons)==8);
}
namespace TotK::Emotes::Controller {
static constexpr uint64_t Down=uint64_t(1)<<15;
static constexpr uint64_t B=uint64_t(1)<<1;
template<class State> static bool ReadStyle(uint32_t id,uint64_t& buttons) {
    State state{};
    if(nn::hid::GetNpadStates(&state,1,id)!=1||(state.attributes&1)==0)return false;
    buttons=state.buttons;
    return true;
}
static bool Read(uint64_t& buttons) {
    buttons=0;
    // Player 1 when docked/emulated; built-in controller when handheld.
    const uint32_t ids[]={0,0x20};
    for(uint32_t id:ids) {
        uint32_t styles=nn::hid::GetNpadStyleSet(id);
        if((styles&1)&&ReadStyle<nn::hid::NpadFullKeyState>(id,buttons))return true;
        if((styles&2)&&ReadStyle<nn::hid::NpadHandheldState>(id,buttons))return true;
        if((styles&4)&&ReadStyle<nn::hid::NpadJoyDualState>(id,buttons))return true;
    }
    return false;
}
}
