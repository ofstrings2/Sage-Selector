#pragma once

#include <wiixlaunch/platform.hpp>
#include <wiixlaunch/hook.hpp>
#include <wiixlaunch/debug_log.hpp>

#if WIIXL_SWITCH

#include <cstdint>
#include <cstring>

namespace TotK::Emotes {

// Public initialization
void Init();

// State
bool IsEmoteWheelActive();

} // namespace TotK::Emotes

#else // !WIIXL_SWITCH

namespace TotK::Emotes {
inline void Init() {}
inline bool IsEmoteWheelActive() { return false; }
}

#endif
