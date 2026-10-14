#include <wiixlaunch.hpp>
#include <wiixlaunch/totk_emotes.hpp>

extern "C" void WiiXLaunch_Init() {
    static bool initialized = false;
    if (initialized) return;
    initialized = true;

    WIIXL_LOG("TotK Emotes: init");

    TotK::Emotes::Init();
}
