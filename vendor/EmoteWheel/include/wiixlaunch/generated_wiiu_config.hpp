#pragma once

#include <cstdint>

#define WUPS_PLUGIN_NAME_STR "EmotesOfTheKingdom"
#define WUPS_PLUGIN_AUTHOR_STR "Nintending"
#define WUPS_PLUGIN_VERSION_STR "1.0.0"
#define WUPS_PLUGIN_DESCRIPTION_STR "Emote Wheel for The Legend of Zelda: Tears of the Kingdom"

namespace WiiXLaunch::WiiUConfig {
    constexpr uint64_t TargetTitleIds[] = { 0x00050000101C9400ULL, 0x00050000101C9500ULL, 0x00050000101C9300ULL };
    constexpr uint32_t TargetTitleIdsCount = sizeof(TargetTitleIds) / sizeof(TargetTitleIds[0]);
}
