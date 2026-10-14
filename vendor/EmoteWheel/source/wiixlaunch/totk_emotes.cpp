#include <wiixlaunch/totk_emotes.hpp>

#if WIIXL_SWITCH

#include <wiixlaunch.hpp>
#include <wiixlaunch/emote_config.hpp>
#include <wiixlaunch/emote_defaults.hpp>
#include <wiixlaunch/emote_input.hpp>
#include <nn/fs.hpp>
#include <wiixlaunch/emote_storage.hpp>
#include <atomic>
#include <cstdio>
#include <cstring>
#include <cstdlib>

namespace TotK::Emotes {

static inline uint32_t StrLen16(const char16_t* s) {
    if (!s) return 0;
    uint32_t len = 0;
    while (*s++) ++len;
    return len;
}

enum class WheelState {
    Idle,
    PendingPress,
    WheelRequested,
    WheelOpen,
    WheelResolved,
    PlayingEmote
};

// Global state
static std::atomic<WheelState> g_WheelState = WheelState::Idle;
static std::atomic<int> g_SelectedEmote = 0;
static std::atomic<int> g_LastEmote = -1;
static uint64_t g_DownPressTick = 0;
static bool g_PressStartedPlaying = false;
static std::atomic<bool> g_IgnoreDownUntilRelease = false;
// An external B/timeout cancellation may run before the whistle action update.
// Finish that action explicitly rather than re-entering vanilla HorseCall logic.
static std::atomic<bool> g_WhistleCompletionPending = false;
static std::atomic<int> g_WheelResult = -1;
static void* g_WheelPauseManager = nullptr;
static uint32_t g_WheelPauseHash = 0;
static bool g_ClosingWheel = false;
static void* g_WheelPrePauseManager = nullptr;
static uint32_t g_WheelPrePauseHash = 0;
static void* g_WheelPreparingBG = nullptr;
static bool g_WheelBackgroundReady = false;
static uint64_t g_WheelPrepareTick = 0;
// Horizon system counter: 19.2 MHz; half a second, independent of frame rate.
static constexpr uint64_t k_WheelHoldTicks = 9600000;
static uint64_t g_EmoteStartTick = 0;
static std::atomic<bool> g_GamePauseActive = false;
static std::atomic<uint64_t> g_GamePauseStarted = 0;
static std::atomic<uint64_t> g_GamePausedTicks = 0;
static std::atomic<bool> g_ResumeCancelGate = false;
static std::atomic<bool> g_PlayerMoveInput = false;
static std::atomic<void*> g_CachedPlayerComp = nullptr;
static std::atomic<void*> g_PendingFaceReset = nullptr;

static ConfigFile::Config g_Config;
static ConfigFile::Config g_PendingConfig;
static char g_EmoteSoundKeys[ConfigFile::MaxEmotes][32]{};
static std::atomic<bool> g_ConfigLoaded = false;
static bool g_ConfigWritable = false;
static std::atomic<int> g_PendingLastUsed = -1;
static std::atomic<bool> g_MusicShouldRestore = false;
static int g_EmoteWheelSlot = -1; // Emote selection, independent of equipped ability.
static void* g_EmoteWheelScreen = nullptr;

static constexpr int s_ActiveWheelCount = 8; // Fixed compass positions, including empty slots.
static int s_ActiveWheelEmotes[8] = {-1,-1,-1,-1,-1,-1,-1,-1};

static uint32_t EmoteIdCrc(const char* name) {
    uint32_t crc=0xffffffff;
    for(const unsigned char* p=reinterpret_cast<const unsigned char*>(name);*p;++p) {
        crc^=*p;
        for(int bit=0;bit<8;++bit)crc=(crc>>1)^(0xedb88320u&uint32_t(-int32_t(crc&1)));
    }
    return ~crc;
}
static void ApplyWheelConfig() {
    for(int i=0;i<g_Config.count;++i)
        std::snprintf(g_EmoteSoundKeys[i],sizeof(g_EmoteSoundKeys[i]),"EmoteWheel_JSON_%08x",EmoteIdCrc(g_Config.emotes[i].id));
    for (int i=0;i<8;++i) s_ActiveWheelEmotes[i]=g_Config.slots[i];
}

// Run from the HUD thread after the filesystem is ready. Publish only a fully
// parsed configuration; the player worker never performs filesystem I/O.
static void EnsureConfigLoaded() {
    if (g_ConfigLoaded.load(std::memory_order_acquire)) return;
    static char library[65536], wheel[4096];
    auto mounted = nn::fs::MountSdCardForDebug("emotesd");
    g_ConfigWritable = mounted == 0;
    const bool loaded = Storage::Read(Storage::Library,library,sizeof(library)) &&
                        Storage::Read(Storage::Wheel,wheel,sizeof(wheel)) &&
                        ConfigFile::Parse(library,wheel,g_PendingConfig);
    if (loaded) g_Config = g_PendingConfig;
    // lastEmoteUsed in old wheel.json files is no longer a runtime save location.
    g_Config.lastEmote = -1;
    if (g_ConfigWritable) {
        int last=-1;
        Storage::LoadLast(g_Config,last);
        g_Config.lastEmote=last;
        g_ConfigWritable=Storage::SaveLast(g_Config,last>=0?g_Config.emotes[last].id:nullptr);
    }
    ApplyWheelConfig();
    g_LastEmote = g_Config.lastEmote;
    g_EmoteWheelSlot = -1;
    for(int i=0;i<8;++i) if(s_ActiveWheelEmotes[i]>=0) {
        if(g_EmoteWheelSlot<0)g_EmoteWheelSlot=i;
        if(s_ActiveWheelEmotes[i]==g_LastEmote){g_EmoteWheelSlot=i;break;}
    }
    g_ConfigLoaded.store(true,std::memory_order_release);
    WIIXL_LOG("TotK Emotes: RomFS JSON loaded=%d; state writable=%d, definitions=%d, last=%d, SD mount=0x%x",
              int(loaded),int(g_ConfigWritable),g_Config.count,int(g_LastEmote.load()),unsigned(mounted));
}

static void FlushLastUsed() {
    const int last=g_PendingLastUsed.exchange(-1);
    if(last<0||last>=g_Config.count)return;
    bool ok=g_ConfigWritable&&Storage::SaveLast(g_Config,g_Config.emotes[last].id);
    WIIXL_LOG("TotK Emotes: lastEmoteUsed=%s, JSON write=%s",g_Config.emotes[last].id,ok?"OK":"FAILED");
}

static uint32_t HudIconKey(const char* name) {
    uint32_t value=2166136261u;
    for(const unsigned char* p=reinterpret_cast<const unsigned char*>(name);*p;++p)
        value=(value^*p)*16777619u;
    return value;
}

bool IsEmoteWheelActive() {
    return g_WheelState != WheelState::Idle;
}

static inline uintptr_t GetBase() {
    return exl::util::modules::GetTargetStart();
}

// Function pointers to engine routines
typedef void* (*GetPlayerComponentFn)(void* executeBase);
typedef void (*PlayCommandFn)(void* playerComp, uint32_t slot, const char* const* commandName, uint32_t flag1, uint32_t flag2);
typedef bool (*GetVirtualKeyHoldValueFn)(void* playerComp, uint32_t virtualKey);
typedef void* (*GetScreenFn)(void* screenMgr, uint32_t nameHash);
typedef void (*ScreenOpenFn)(void* screen, int option);
typedef void (*ScreenCloseFn)(void* screen, int option);
typedef void (*SetRotationFn)(void* partsScreen, float angle);
typedef void (*SetValidFn)(void* partsScreen, bool isValid);
typedef void (*DoOutBeforeFn)(void* screen, bool isCancel);
typedef void* (*FindPaneByPathFn)(void* layout, const char* path);
typedef ulong (*SetStringFn)(void* textBoxPane, const char16_t* str, ulong dstOffset, uint32_t length);
static GetPlayerComponentFn s_GetPlayerComponent = nullptr;
static PlayCommandFn s_PlayCommand = nullptr;
// Native face-only AS application, PlayerComponent +0xb74, at 0x006a1208.
using SetFaceCommandFn = void (*)(void*, const char* const*, uint64_t);
static SetFaceCommandFn s_SetFaceCommand = nullptr;
static GetVirtualKeyHoldValueFn s_GetVirtualKeyHoldValue = nullptr;
static GetScreenFn s_GetScreenMain = nullptr;
static GetScreenFn s_GetScreenBG = nullptr;
static ScreenOpenFn s_ScreenOpen = nullptr;
static void (*s_PrepareShortCutCapture)(void*) = nullptr;
static void (*s_RequestShortCutCapture)(void*) = nullptr;
static ScreenCloseFn s_ScreenClose = nullptr;
static SetRotationFn s_SetRotation = nullptr;
static SetValidFn s_SetValid = nullptr;
static DoOutBeforeFn s_DoOutBefore = nullptr;
static FindPaneByPathFn s_FindPaneByPath = nullptr;
static SetStringFn s_SetString = nullptr;
using PartSelectionFn = void (*)(void*,uint64_t);
static PartSelectionFn s_SetCheck = nullptr;
static PartSelectionFn s_SelectPart = nullptr;
static PartSelectionFn s_UnselectPart = nullptr;
using SetWheelIconFn = uint64_t (*)(void*,const char* const*,void*);
static SetWheelIconFn s_SetWheelIcon = nullptr;
using HashNameFn = uint32_t (*)(const char*,uint32_t);
using ReleaseDuckingFn = void (*)(void*,uint32_t,uint32_t);
static HashNameFn s_HashName = nullptr;
static ReleaseDuckingFn s_ReleaseDucking = nullptr;
using PauseRequestFn = uint64_t (*)(uint32_t);
static PauseRequestFn s_RequestPause = nullptr;
static PauseRequestFn s_ReleasePause = nullptr;
// HID remains live when the engine returns neutral UI/player controllers.
static uint64_t g_LastControllerMask=0;
static bool ReadWheelInput(bool& down, bool& cancel) {
    uint64_t buttons=0;
    const bool connected=Controller::Read(buttons);
    g_LastControllerMask=buttons;
    down=(buttons&Controller::Down)!=0;
    cancel=(buttons&Controller::B)!=0;
    return connected;
}

static bool AcquireNamedPause(const char* name, void*& owner, uint32_t& ownedHash) {
    if(owner)return true;
    if(!s_RequestPause||!s_ReleasePause||!s_HashName)return false;
    void* mgr=*reinterpret_cast<void**>(GetBase()+0x04728688);
    if(!mgr){WIIXL_LOG("TotK Emotes: wheel pause unavailable; no PauseMgr");return false;}
    // RequestPause's return means zero-to-one transition, not success.
    // Check the request exists; acquire one count even if another menu owns one.
    uint32_t count=*static_cast<uint32_t*>(mgr);
    char* entries=*reinterpret_cast<char**>(static_cast<char*>(mgr)+8);
    if(!entries||count>4096){WIIXL_LOG("TotK Emotes: wheel pause unavailable; table count=%u",count);return false;}
    uint32_t hash=s_HashName(name,0);
    for(uint32_t i=0;i<count;++i) {
        if(*reinterpret_cast<uint32_t*>(entries+i*0x20+8)!=hash)continue;
        s_RequestPause(hash);owner=mgr;ownedHash=hash;
        return true;
    }
    WIIXL_LOG("TotK Emotes: %s request not found; hash=0x%x, count=%u",name,hash,count);
    return false;
}
static void ReleaseNamedPause(void*& owner, uint32_t ownedHash) {
    if(!owner)return;
    if(s_ReleasePause&&owner==*reinterpret_cast<void**>(GetBase()+0x04728688))
        s_ReleasePause(ownedHash);
    owner=nullptr;
}
static bool AcquireWheelPause() {
    return AcquireNamedPause("GamePause",g_WheelPauseManager,g_WheelPauseHash);
}
static void ReleaseWheelPause() {
    ReleaseNamedPause(g_WheelPauseManager,g_WheelPauseHash);
}
// ResourceAccessorSLink::getDelayWithOverwrite, verified at 0x022957d8.
// Return a per-emote delay only for the tool's private cloned sound assets.
// Native XLink owns the delayed request, including cancellation and pause.
WIIXL_HOOK_DEFINE_TRAMPOLINE(EmoteSoundDelayHook) {
    static float Callback(void* accessor, void* table, void* overwrite, void* user, void* context) {
        if(table&&g_ConfigLoaded.load(std::memory_order_acquire)) {
            const char* name=*static_cast<const char* const*>(table);
            if(name&&!std::strncmp(name,"EmoteWheel_JSON_",15)) {
                for(int i=0;i<g_Config.count;++i)
                    if(!std::strcmp(name,g_EmoteSoundKeys[i]))return float(g_Config.emotes[i].musicDelayMs)*0.03f;
            }
        }
        return Orig(accessor,table,overwrite,user,context);
    }
};
// Observe native zero/one GamePause transitions without changing pause ownership.
static void ObserveGamePause(bool paused) {
    const uint64_t now=svcGetSystemTick();
    if(paused) {
        g_GamePauseStarted=now;
        g_GamePauseActive=true;
    } else if(g_GamePauseActive.load()) {
        g_GamePausedTicks.fetch_add(now-g_GamePauseStarted.load());
        g_ResumeCancelGate=true; // B used to leave a menu is not overworld cancel.
        g_GamePauseActive=false;
    }
}
static uint64_t EmoteClockTicks() {
    const uint64_t now=g_GamePauseActive.load()?g_GamePauseStarted.load():svcGetSystemTick();
    const uint64_t paused=g_GamePausedTicks.load();
    return now>=paused?now-paused:0;
}
WIIXL_HOOK_DEFINE_TRAMPOLINE(EmotePauseRequestHook) {
    static uint64_t Callback(uint32_t hash) {
        const uint64_t transition=Orig(hash);
        if(transition&&s_HashName&&hash==s_HashName("GamePause",0))ObserveGamePause(true);
        return transition;
    }
};
WIIXL_HOOK_DEFINE_TRAMPOLINE(EmotePauseReleaseHook) {
    static uint64_t Callback(uint32_t hash) {
        const uint64_t transition=Orig(hash);
        if(transition&&s_HashName&&hash==s_HashName("GamePause",0))ObserveGamePause(false);
        return transition;
    }
};
static bool EmoteHasEnded(int emote) {
    if(emote<0||emote>=g_Config.count)return true;
    const auto& e=g_Config.emotes[emote];
    const uint64_t now=EmoteClockTicks();
    return !e.loop&&now>=g_EmoteStartTick&&now-g_EmoteStartTick >=
        (uint64_t(e.durationMs)+e.musicDelayMs)*19200;
}
static bool HasPlayingEmote() {
    return g_WheelState==WheelState::PlayingEmote ||
        (g_WheelState==WheelState::PendingPress&&g_PressStartedPlaying);
}

static void ReleaseEmoteDucking() {
    if(!s_HashName||!s_ReleaseDucking)return;
    // Native OneShotSoundReleaseDucking uses SoundMgr -> manual-ducker manager.
    void* sound=*reinterpret_cast<void**>(GetBase()+0x047198b8);
    if(!sound)return;
    void* duckers=*reinterpret_cast<void**>(static_cast<char*>(sound)+0x60);
    if(duckers)s_ReleaseDucking(duckers,s_HashName("EmoteWheelMusic",0),0);
}

static void RestoreMusic() {
    g_MusicShouldRestore=true;
    ReleaseEmoteDucking();
}


// Retrieve the active ScreenMgr instance from .bss (0x0471ae40)
static inline void* GetScreenMgr() {
    uintptr_t base = GetBase();
    uintptr_t* pInstance = (uintptr_t*)(base + 0x0471ae40);
    if (!pInstance || !*pInstance) {
        return nullptr;
    }
    return (void*)*pInstance;
}

// Safe extraction of PlayerComponent from AI execution node
static inline void* ExtractPlayerComponent(void* thisPtr) {
    if (!thisPtr) return nullptr;
    uintptr_t p = (uintptr_t)thisPtr;
    uintptr_t a = *(uintptr_t*)(p + 8);
    if (!a) return nullptr;
    uintptr_t b = *(uintptr_t*)(a + 8);
    if (!b) return nullptr;
    uintptr_t c = *(uintptr_t*)(b + 0x1f8);
    if (!c) return nullptr;
    uintptr_t d = *(uintptr_t*)(c + 0x228);
    if (!d) return nullptr;
    return (void*)*(uintptr_t*)(d + 0x3a8);
}

// Reset the four body layers at both priorities to stop the AS[0] sound.
// Face uses its own FaceDefault command; Wait is not a facial animation.
static void StopPlayingEmote() {
    if(HasPlayingEmote())RestoreMusic();
    if (HasPlayingEmote() && g_CachedPlayerComp && s_PlayCommand) {
        static const char* const waitCommand = "Wait";
        s_PlayCommand(g_CachedPlayerComp, 0, &waitCommand, 0x0f, 4);
        s_PlayCommand(g_CachedPlayerComp, 1, &waitCommand, 0x0f, 4);
        g_PendingFaceReset=g_CachedPlayerComp.load();
    }
}

// The whistle action can be interrupted by B before its next update. Monitor
// cancellation immediately before the engine consumes player AS requests.
static void CheckOverworldEmote() {
    if(!HasPlayingEmote()||g_GamePauseActive.load())return;
    uint64_t buttons=0;
    const bool input=Controller::Read(buttons);
    const bool b=input&&(buttons&Controller::B);
    if(input&&!b)g_ResumeCancelGate=false;
    // Movement owns action completion in the whistle update. Clearing Playing
    // here makes that update fall through to HorseCall, which never completes
    // while our emote AS is active. This also applies to simultaneous B/move.
    if(g_PlayerMoveInput.load())return;
    const bool cancel=b&&!g_ResumeCancelGate.load();
    if(cancel||EmoteHasEnded(g_SelectedEmote.load())) {
        StopPlayingEmote();
        g_PressStartedPlaying=false;
        g_WhistleCompletionPending=true;
        g_WheelState=WheelState::Idle;
        WIIXL_LOG("TotK Emotes: AS dispatch cancel emote=%d reason=%s",int(g_SelectedEmote.load()),cancel?"B":"ended");
        // No Down latch is set: the next tap is immediately available.
    }
}

// PlayerComponent AS dispatch (0x0069dbc4) reads the priority request buffers
// written by PlayCommand. Unlike camera calculation, this is the consumption
// point: later AI calculations cannot replace the cancellation before dispatch.
// It also runs when B has interrupted the whistle action's update.
WIIXL_HOOK_DEFINE_TRAMPOLINE(PlayerEmoteASUpdateHook) {
    static void Callback(void* player) {
        if(player&&player==g_CachedPlayerComp.load())CheckOverworldEmote();
        Orig(player);
        // Apply once after native selection, so a lingering emote expression
        // cannot win this frame. Keep it scoped to the component we cancelled.
        if(player&&player==g_CachedPlayerComp.load()&&!HasPlayingEmote()&&
           !g_GamePauseActive.load()&&s_SetFaceCommand) {
            void* expected=player;
            if(g_PendingFaceReset.compare_exchange_strong(expected,nullptr)) {
                static const char* const faceDefault="FaceDefault";
                s_SetFaceCommand(player,&faceDefault,1);
            }
        }
    }
};

// Player camera input calculation, verified in this 1.2.1 main at 0x00d17e60.
// The AI parameter at +0x20 points to a pointer to the 0x4c-byte input value.
// Use a local copy for this calculation; UI selection keeps the original stick.
WIIXL_HOOK_DEFINE_TRAMPOLINE(PlayerCameraInputHook) {
    static void Callback(void* thisPtr, void* calcContext) {
        if (!thisPtr) { Orig(thisPtr, calcContext); return; }
        auto& binding = *reinterpret_cast<float***>(static_cast<char*>(thisPtr) + 0x20);
        if (!binding || !*binding) { Orig(thisPtr, calcContext); return; }
        const float* input = *binding;
        g_PlayerMoveInput = input[2] * input[2] + input[3] * input[3] > 0.04f;
        if (g_WheelState != WheelState::WheelOpen) { Orig(thisPtr, calcContext); return; }
        alignas(16) float neutral[19];
        std::memcpy(neutral, input, sizeof(neutral));
        neutral[0] = neutral[1] = 0.0f;
        // Disable gyro for this camera calculation as well (sample count at +0x18).
        neutral[6] = 0.0f;
        for (int i = 7; i < 19; ++i) neutral[i] = 0.0f;
        neutral[10] = neutral[14] = neutral[18] = 1.0f;
        float* neutralPtr = neutral;
        float** originalBinding = binding;
        binding = &neutralPtr;
        Orig(thisPtr, calcContext);
        binding = originalBinding;
    }
};

// --------------------------------------------------------------------------
// Emote Wheel Radial Menu Hooks
// --------------------------------------------------------------------------

// Down is reserved while deciding between a tap and a hold.
static void BeginDownPress() {
    g_PressStartedPlaying = g_WheelState==WheelState::PlayingEmote;
    g_DownPressTick = svcGetSystemTick();
    g_WheelState = WheelState::PendingPress;
}

static bool StartEmote(void* playerComp, int emote) {
    if (!playerComp || !s_PlayCommand || emote < 0 || emote >= g_Config.count) return false;
    g_MusicShouldRestore=false;
    g_PendingFaceReset=nullptr;
    g_WhistleCompletionPending=false;
    g_SelectedEmote = emote;
    const char* command = g_Config.emotes[emote].asCommand;
    s_PlayCommand(playerComp, 0, &command, 0x1f, 0x84);
    // Priority 1 must include the base/lower-body layer as well as upper body.
    s_PlayCommand(playerComp, 1, &command, 0x1f, 4);
    g_LastEmote = emote;
    g_PendingLastUsed.store(emote);
    g_WheelState = WheelState::PlayingEmote;
    g_EmoteStartTick = EmoteClockTicks();
    return true;
}

// Screen/pause operations belong to the UI thread. The player worker queues
// an open and consumes its result after gameplay resumes.
static void AbortWheelPreparation() {
    void* mgr=GetScreenMgr();
    void* bg=mgr&&s_GetScreenBG?s_GetScreenBG(mgr,0xc5a49707):nullptr;
    if(g_WheelPreparingBG&&bg==g_WheelPreparingBG&&s_ScreenClose)s_ScreenClose(bg,-1);
    g_WheelPreparingBG=nullptr;
    g_WheelBackgroundReady=false;
    ReleaseNamedPause(g_WheelPrePauseManager,g_WheelPrePauseHash);
}
static void OpenEmoteWheel() {
    void* mgr=GetScreenMgr();
    void* main=mgr&&s_GetScreenMain?s_GetScreenMain(mgr,0x691f2be1):nullptr;
    void* bg=mgr&&s_GetScreenBG?s_GetScreenBG(mgr,0xc5a49707):nullptr;
    bool down=false,cancel=false;
    const bool input=ReadWheelInput(down,cancel);
    const bool ready=main&&bg&&s_ScreenOpen&&s_PrepareShortCutCapture&&
        s_RequestShortCutCapture&&input&&!cancel&&down;
    bool paused=false;
    if(ready) {
        if(!g_WheelPreparingBG) {
            // ShortCutPauseOn.module: first open BG with capture-before disabled
            // and PreGamePause. Its next sequential group runs on a later frame.
            if(AcquireNamedPause("PreGamePause",g_WheelPrePauseManager,g_WheelPrePauseHash)) {
                s_PrepareShortCutCapture(bg);
                s_ScreenOpen(bg,1);
                g_WheelPreparingBG=bg;
                g_WheelBackgroundReady=false;
                g_WheelPrepareTick=svcGetSystemTick();
                return;
            }
        } else if(bg==g_WheelPreparingBG) {
            // ScreenOpen queues the animation; it does not finish opening.
            // Normal-wheel traces enter main with BG state 2 and opacity 255.
            // Our old one-frame delay captured state 1, while capture panes were
            // still hidden. Wait for native open completion, then allow that
            // completed background a render frame before acquiring GamePause.
            const bool openComplete=static_cast<uint8_t*>(bg)[0x16e]==2;
            const bool timedOut=svcGetSystemTick()-g_WheelPrepareTick>57600000;
            if(!timedOut) {
                if(!openComplete){g_WheelBackgroundReady=false;return;}
                if(!g_WheelBackgroundReady) {
                    g_WheelBackgroundReady=true;
                    WIIXL_LOG("TotK Emotes: background fully open; waiting one render frame before capture");
                    return;
                }
                paused=AcquireWheelPause();
            } else WIIXL_LOG("TotK Emotes: background opening timed out; cancelling safely");
        }
    }
    if(!paused) {
        WIIXL_LOG("TotK Emotes: wheel open rejected; main=%d bg=%d input=%d down=%d B=%d pause=%d HID=0x%llx",
            int(main!=nullptr),int(bg!=nullptr),int(input),int(down),int(cancel),int(paused),static_cast<unsigned long long>(g_LastControllerMask));
        AbortWheelPreparation();
        g_WheelResult=-1;g_IgnoreDownUntilRelease=true;
        g_WheelState=WheelState::WheelResolved;return;
    }
    // Native second group: capture BG + GamePause, then release PreGamePause.
    // Capture-before also prevents lower UI layers from invalidating the snapshot.
    s_RequestShortCutCapture(bg);
    g_WheelPreparingBG=nullptr;
    g_WheelBackgroundReady=false;
    ReleaseNamedPause(g_WheelPrePauseManager,g_WheelPrePauseHash);
    g_EmoteWheelScreen=main;
    g_SelectedEmote=g_EmoteWheelSlot>=0?s_ActiveWheelEmotes[g_EmoteWheelSlot]:-1;
    g_WheelState=WheelState::WheelOpen;
    s_ScreenOpen(main,1);
    WIIXL_LOG("TotK Emotes: wheel opened with native background capture and GamePause; HID=0x%llx",static_cast<unsigned long long>(g_LastControllerMask));
}
static void CloseEmoteWheel(bool cancel, bool resolve=true) {
    if((g_WheelState!=WheelState::WheelOpen&&!g_WheelPauseManager)||g_ClosingWheel)return;
    g_ClosingWheel=true;
    void* mgr=GetScreenMgr();
    void* main=g_EmoteWheelScreen;
    void* bg=mgr&&s_GetScreenBG?s_GetScreenBG(mgr,0xc5a49707):nullptr;
    if(main) {
        if(s_DoOutBefore)s_DoOutBefore(main,cancel);
        if(s_ScreenClose)s_ScreenClose(main,-1);
    }
    if(bg&&s_ScreenClose)s_ScreenClose(bg,-1);
    g_WheelResult=cancel?-1:g_SelectedEmote.load();
    if(cancel)g_IgnoreDownUntilRelease=true;
    ReleaseWheelPause();g_WheelState=resolve?WheelState::WheelResolved:WheelState::Idle;
    g_ClosingWheel=false;
    WIIXL_LOG("TotK Emotes: wheel closed; cancel=%d; GamePause released",int(cancel));
}
static void UpdateWheelUI() {
    if(g_WheelState!=WheelState::WheelRequested&&g_WheelState!=WheelState::WheelOpen&&
       !g_IgnoreDownUntilRelease&&!g_WheelPauseManager&&!g_WheelPreparingBG&&!g_WheelPrePauseManager)return;
    bool down=false,cancel=false;
    const bool input=ReadWheelInput(down,cancel);
    if(input&&!down)g_IgnoreDownUntilRelease=false;
    if(g_WheelState==WheelState::WheelRequested)OpenEmoteWheel();
    if(g_WheelState==WheelState::WheelOpen) {
        // B wins even if Down is released on the same frame.
        if(!input||cancel)CloseEmoteWheel(true);
        else if(!down)CloseEmoteWheel(false);
    } else if(g_WheelState!=WheelState::WheelRequested&&(g_WheelPreparingBG||g_WheelPrePauseManager)) {
        AbortWheelPreparation();
    } else if(g_WheelPauseManager) {
        // A reload/invalidated player can end its worker while the UI is open.
        // Close both screens without queuing an action for the new player.
        CloseEmoteWheel(true,false);
    }
}

// UIPlayerStatusScreen::updateImpl_ (1.2.1). Resolve our own panes on each
// update so a rebuilt HUD never leaves cached pointers to freed layouts.
// Native CtrlGuide uses Pane +0x59 for alpha (0x01aedc30); ancestor alpha
// still controls HUD fading. These pictures have no animation tracks.
WIIXL_HOOK_DEFINE_TRAMPOLINE(PlayerStatusRepeatIconHook) {
    static void Callback(void* thisPtr) {
        Orig(thisPtr);
        UpdateWheelUI();
        if (!thisPtr || !s_FindPaneByPath) return;
        void* layout = *(void**)((char*)thisPtr + 0x28);
        if (!layout) return;
        EnsureConfigLoaded();
        FlushLastUsed();
        // Cancellation and native asset shutdown can land on different threads.
        // Clear late requests while stopped; only our named ducker is affected.
        if(g_MusicShouldRestore.load())ReleaseEmoteDucking();
        const int last=g_LastEmote.load();
        const char* selected=(last>=0&&last<g_Config.count)?g_Config.emotes[last].bntx:"";
        for (int i=0;i<g_Config.count;++i) {
            const char* icon=g_Config.emotes[i].bntx;
            if(!*icon)continue;
            char path[64];
            std::snprintf(path,sizeof(path),"Pa_ShortCutGuide_00/P_EmoteIcon_%08x",HudIconKey(icon));
            void* pane=s_FindPaneByPath(layout,path);
            if(pane)*(uint8_t*)((char*)pane+0x59)=!std::strcmp(icon,selected)?255:0;
        }
    }
};

// Hook 1: ExecutePlayerWhistle::calc (0x7101d8fee0)
WIIXL_HOOK_DEFINE_TRAMPOLINE(ExecutePlayerWhistleCalcHook) {
    static void Callback(void* thisPtr) {
        if (!thisPtr) { Orig(thisPtr); return; }
        if(!g_ConfigLoaded.load(std::memory_order_acquire)){Orig(thisPtr);return;}
        void* player = s_GetPlayerComponent ? s_GetPlayerComponent(thisPtr) : nullptr;
        if (!player) player = ExtractPlayerComponent(thisPtr);
        if (!player) { Orig(thisPtr); return; }
        if (g_CachedPlayerComp == player &&
            (g_IgnoreDownUntilRelease || g_WheelState==WheelState::PendingPress ||
             g_WheelState==WheelState::WheelRequested || g_WheelState==WheelState::WheelOpen ||
             g_WheelState==WheelState::WheelResolved)) {
            *(char*)((char*)thisPtr + 0x20) = 0;return;
        }
        if(g_CachedPlayerComp!=player) {
            if(HasPlayingEmote())RestoreMusic();
            g_WheelState=WheelState::Idle;
        }
        g_CachedPlayerComp=player;
        g_WhistleCompletionPending=false;
        BeginDownPress();
        *(char*)((char*)thisPtr + 0x20) = 0;
    }
};

// Hook 2: ExecutePlayerWhistle::updateImpl_ (0x7101d8ffcc)
WIIXL_HOOK_DEFINE_TRAMPOLINE(ExecutePlayerWhistleUpdateHook) {
    static void Callback(void* thisPtr) {
        if (!thisPtr) return;
        if (g_WheelState == WheelState::Idle) {
            if(g_WhistleCompletionPending.load()) {
                *(char*)((char*)thisPtr+0x20)=1;
                return;
            }
            Orig(thisPtr); return;
        }
        void* player = ExtractPlayerComponent(thisPtr);
        if(player!=g_CachedPlayerComp.load()) {
            // A save reload can invalidate the old component before the next press.
            RestoreMusic();g_WheelState=WheelState::Idle;g_CachedPlayerComp=player;
            *(char*)((char*)thisPtr+0x20)=1;return;
        }
        if (!player || !s_GetVirtualKeyHoldValue) {
            RestoreMusic();
            g_WheelState = WheelState::Idle;
            *(char*)((char*)thisPtr + 0x20) = 1;
            return;
        }
        if(g_GamePauseActive.load())return;
        const bool held = s_GetVirtualKeyHoldValue(player, 0x12);
        uint64_t physicalButtons=0;
        if(Controller::Read(physicalButtons)&&!(physicalButtons&Controller::B))g_ResumeCancelGate=false;
        const bool cancelB=((physicalButtons&Controller::B)||s_GetVirtualKeyHoldValue(player,1))&&
            !g_ResumeCancelGate.load();
        *(char*)((char*)thisPtr + 0x20) = 0;
        if(g_WheelState==WheelState::WheelResolved) {
            int result=g_WheelResult.exchange(-1);
            if(!StartEmote(player,result)) {
                g_WheelState=WheelState::Idle;
                *(char*)((char*)thisPtr+0x20)=1;
            }
            return;
        }
        if(g_WheelState==WheelState::WheelRequested||g_WheelState==WheelState::WheelOpen)return;
        if (g_WheelState == WheelState::PendingPress) {
            if(g_PressStartedPlaying) {
                bool stopped=g_PlayerMoveInput||cancelB||
                    s_GetVirtualKeyHoldValue(player,2)||s_GetVirtualKeyHoldValue(player,3);
                bool ended=EmoteHasEnded(g_SelectedEmote.load());
                if(stopped||ended){StopPlayingEmote();g_PressStartedPlaying=false;}
            }
            if(cancelB) {
                g_IgnoreDownUntilRelease=true;g_WheelState=WheelState::Idle;
                *(char*)((char*)thisPtr+0x20)=1;
            } else if (!held) {
                if(g_PressStartedPlaying&&g_SelectedEmote==g_LastEmote) {
                    g_WheelState=WheelState::PlayingEmote; // Keep animation/audio position.
                    WIIXL_LOG("TotK Emotes: repeat ignored; emote already playing");
                } else if (!StartEmote(player, g_LastEmote)) {
                    g_WheelState=WheelState::Idle;
                    *(char*)((char*)thisPtr+0x20)=1;
                }
                g_PressStartedPlaying=false;
            } else if (svcGetSystemTick()-g_DownPressTick>=k_WheelHoldTicks) {
                StopPlayingEmote();g_PressStartedPlaying=false;
                g_WheelState=WheelState::WheelRequested;
                WIIXL_LOG("TotK Emotes: Down hold threshold reached; opening requested");
            }
            return;
        }
        if (g_WheelState == WheelState::PlayingEmote) {
            if (held&&!g_IgnoreDownUntilRelease) { BeginDownPress(); return; }

            const bool cancel = g_PlayerMoveInput ||
                cancelB || // B
                s_GetVirtualKeyHoldValue(player, 2) || // X
                s_GetVirtualKeyHoldValue(player, 3);   // Y
            if (cancel || EmoteHasEnded(g_SelectedEmote.load())) {
                StopPlayingEmote();
                g_WheelState = WheelState::Idle;
                *(char*)((char*)thisPtr + 0x20) = 1;
            }
        }
    }
};

// Bounded diagnostics compare the same native background in both wheel paths.
static void* g_CaptureTraceScreen=nullptr;
static int g_CaptureTraceFrame=0;
static bool g_CaptureTraceEmote=false;
static void TraceWheelCapture(const char* phase) {
    void* mgr=GetScreenMgr();
    void* bg=mgr&&s_GetScreenBG?s_GetScreenBG(mgr,0xc5a49707):nullptr;
    if(!bg){WIIXL_LOG("TotK Emotes: capture trace %s %s missing BG",g_CaptureTraceEmote?"emote":"ability",phase);return;}
    auto* b=static_cast<uint8_t*>(bg);
    void* layout=*reinterpret_cast<void**>(b+0x28);
    WIIXL_LOG("TotK Emotes: capture trace %s %s frame=%d state=%u request=%u flags=%x/%x layout=%d",
        g_CaptureTraceEmote?"emote":"ability",phase,g_CaptureTraceFrame,
        unsigned(b[0x16e]),unsigned(b[0x16d]),unsigned(b[0x175]),unsigned(b[0x176]),int(layout!=nullptr));
    if(layout&&s_FindPaneByPath) {
        const char* names[]={"RootPane","N_BG_00","C_CaptureBG_00","P_CaptureBG_00","C_CaptureClearBG_00","P_CaptureClearBG_00"};
        for(const char* name:names) {
            auto* pane=static_cast<uint8_t*>(s_FindPaneByPath(layout,name));
            if(pane)WIIXL_LOG("TotK Emotes: capture pane %s flags=%x alpha=%u",name,unsigned(pane[0x58]),unsigned(pane[0x59]));
            else WIIXL_LOG("TotK Emotes: capture pane %s missing",name);
        }
    }
}

// Hook 3: UIShortCutMainItemScreen::openStartImpl_ (0x7101b1dc94)
// Distributes active equipped emotes radially
WIIXL_HOOK_DEFINE_TRAMPOLINE(UIShortCutMainItemOpenStartHook) {
    static void Callback(void* thisPtr) {
        Orig(thisPtr);
        g_CaptureTraceScreen=thisPtr;g_CaptureTraceFrame=0;
        g_CaptureTraceEmote=g_WheelState==WheelState::WheelOpen;
        TraceWheelCapture("open");


        if (g_WheelState != WheelState::WheelOpen || !thisPtr) {
            return;
        }

        uint32_t numParts = *(uint32_t*)((char*)thisPtr + 0x1a8);
        void** partsList = *(void***)((char*)thisPtr + 0x1b0);

        g_EmoteWheelScreen=thisPtr;
        if(g_EmoteWheelSlot<0||g_EmoteWheelSlot>=8||s_ActiveWheelEmotes[g_EmoteWheelSlot]<0) {
            g_EmoteWheelSlot=-1;
            for(int i=0;i<8;++i)if(s_ActiveWheelEmotes[i]>=0){g_EmoteWheelSlot=i;break;}
        }
        g_SelectedEmote=g_EmoteWheelSlot<0?-1:s_ActiveWheelEmotes[g_EmoteWheelSlot];
        *(int*)((char*)thisPtr+0x23c)=g_EmoteWheelSlot;
        *(int*)((char*)thisPtr+0x240)=g_EmoteWheelSlot;
        *(uint8_t*)((char*)thisPtr+0x245)=g_EmoteWheelSlot>=0;
        *(uint64_t*)((char*)thisPtr+0x254)=0; // Clear ability-wheel stick history.
        float degrees=g_EmoteWheelSlot<0?90.0f:90.0f-45.0f*g_EmoteWheelSlot;
        if(degrees<0)degrees+=360.0f;
        float radians=degrees*0.017453292519943295f;
        *(float*)((char*)thisPtr+0x228)=radians;
        *(float*)((char*)thisPtr+0x22c)=radians;
        void* cursor=*(void**)((char*)thisPtr+0x220);
        if(cursor) {
            *(uint64_t*)((char*)cursor+0x3c)=0;
            *(float*)((char*)cursor+0x44)=degrees;
            *(uint8_t*)((char*)cursor+0x58)|=0x10;
        }
        int count = s_ActiveWheelCount;
        for (uint32_t i = 0; i < 8; ++i) {
            if(i<numParts&&partsList&&partsList[i]) {
                bool selected=int(i)==g_EmoteWheelSlot;
                if(s_SetCheck)s_SetCheck(partsList[i],selected);
                if(selected&&s_SelectPart)s_SelectPart(partsList[i],1);
                if(!selected&&s_UnselectPart)s_UnselectPart(partsList[i],1);
            }
            if ((int)i < count && s_ActiveWheelEmotes[i] >= 0) {
                *(int*)((char*)thisPtr + 0x270 + i * 4) = (int)(i + 1);

                if (i < numParts && partsList && partsList[i]) {
                    if(s_SetWheelIcon) {
                        const char* icon=g_Config.emotes[s_ActiveWheelEmotes[i]].bntx;
                        if(*icon) {
                            char path[192];
                            int size=std::snprintf(path,sizeof(path),"UI/Tex/Icon/%s.bntx",icon);
                            if(size>0&&size<int(sizeof(path))) {
                                const char* name=path;
                                s_SetWheelIcon(partsList[i],&name,(char*)thisPtr+0x1b8);
                            }
                        }
                    }
                    if (s_SetRotation) {
                        float angle = (360.0f / (float)count) * (float)i;
                        s_SetRotation(partsList[i], angle);
                    }
                    if (s_SetValid) {
                        s_SetValid(partsList[i], true);
                    }
                }
            } else {
                *(int*)((char*)thisPtr + 0x270 + i * 4) = 0;
                if (i < numParts && partsList && partsList[i]) {
                    if (s_SetValid) {
                        s_SetValid(partsList[i], false);
                    }
                }
            }
        }
    }
};

// Hook 4: UIShortCutMainItemScreen::updateImpl_ (0x7101b1e65c)
WIIXL_HOOK_DEFINE_TRAMPOLINE(UIShortCutMainItemUpdateHook) {
    static void Callback(void* thisPtr) {
        if(thisPtr&&thisPtr==g_EmoteWheelScreen&&g_WheelState==WheelState::WheelOpen) {
            bool down=false,cancel=false;
            if(!ReadWheelInput(down,cancel)||cancel){CloseEmoteWheel(true);return;}
        }
        Orig(thisPtr);
        if(thisPtr&&thisPtr==g_CaptureTraceScreen&&g_CaptureTraceFrame<6) {
            ++g_CaptureTraceFrame;TraceWheelCapture("update");
        }


        if (g_WheelState != WheelState::WheelOpen || !thisPtr) {
            return;
        }

        if(thisPtr!=g_EmoteWheelScreen)return;
        g_SelectedEmote = -1;
        int slot = *(int*)((char*)thisPtr + 0x23c);
        if (slot >= 0 && slot < s_ActiveWheelCount) {
            int emoteIdx = s_ActiveWheelEmotes[slot];
            if (emoteIdx >= 0 && emoteIdx < g_Config.count) {
                g_SelectedEmote = emoteIdx;
                // Hover is provisional; only confirmation updates g_EmoteWheelSlot.
                void* layout = *(void**)((char*)thisPtr + 0x28);
                if (layout && s_FindPaneByPath && s_SetString) {
                    void* textPane = s_FindPaneByPath(layout, "T_Text_00");
                    if (textPane) {
                        const char16_t* nameU16 = g_Config.emotes[emoteIdx].label;
                        s_SetString(textPane, nameU16, 0, StrLen16(nameU16));
                    }
                }
            }
        } else if (s_ActiveWheelCount == 0) {
            g_SelectedEmote = -1;
        }
        UpdateWheelUI();


    }
};

// Hook 5: UIShortCutMainItemScreen::doOutBeforeImpl_ (0x7101b1eef8)
WIIXL_HOOK_DEFINE_TRAMPOLINE(UIShortCutMainItemDoOutBeforeHook) {
    static void Callback(void* thisPtr) {
        if (!thisPtr || thisPtr!=g_EmoteWheelScreen) {
            Orig(thisPtr);
            return;
        }

        int selectedIndex = *(int*)((char*)thisPtr + 0x23c);
        if (selectedIndex >= 0 && selectedIndex < s_ActiveWheelCount) {
            g_SelectedEmote = s_ActiveWheelEmotes[selectedIndex];
            if(g_SelectedEmote>=0)g_EmoteWheelSlot=selectedIndex;
        } else {
            g_SelectedEmote = -1;
        }

        *(char*)((char*)thisPtr + 0x244) = 1;
    }
};

// Hook 6: UIShortCutMainItemScreen::closeEndImpl_ (0x7101b1eeb8)
WIIXL_HOOK_DEFINE_TRAMPOLINE(UIShortCutMainItemCloseEndHook) {
    static void Callback(void* thisPtr) {
        Orig(thisPtr);
        if(thisPtr!=g_EmoteWheelScreen)return;
        g_EmoteWheelScreen=nullptr;
        if(g_WheelState==WheelState::WheelOpen&&!g_ClosingWheel) {
            // Main has already closed: close only its background and release pause.
            CloseEmoteWheel(true);
        }
    }
};

// Hook 7: _LocalModule_cf31571495c4Module::select_ (0x710109db80)
WIIXL_HOOK_DEFINE_TRAMPOLINE(DpadSelectHook) {
    static void Callback(void* thisPtr) {
        if (g_IgnoreDownUntilRelease || g_WheelState == WheelState::WheelOpen ||
            g_WheelState == WheelState::WheelRequested || g_WheelState == WheelState::WheelResolved ||
            g_WheelState == WheelState::PendingPress) {
            return;
        }
        Orig(thisPtr);
    }
};

void Init() {
    WIIXL_LOG("TotK Emotes: Initializing pause-aware emote timing and persistent cancel cleanup...");

    uintptr_t base = GetBase();

    // Resolve engine routine addresses
    s_GetPlayerComponent = (GetPlayerComponentFn)(base + 0x0107e9a0);
    s_PlayCommand = (PlayCommandFn)(base + 0x00bf82b4);
    s_SetFaceCommand = (SetFaceCommandFn)(base + 0x006a1208);
    s_GetVirtualKeyHoldValue = (GetVirtualKeyHoldValueFn)(base + 0x01d2c004);
    s_GetScreenMain = (GetScreenFn)(base + 0x019a3610);
    s_GetScreenBG = (GetScreenFn)(base + 0x019ad66c);
    s_ScreenOpen = (ScreenOpenFn)(base + 0x02a69044);
    s_PrepareShortCutCapture=reinterpret_cast<void(*)(void*)>(base+0x019ad6d4);
    s_RequestShortCutCapture=reinterpret_cast<void(*)(void*)>(base+0x019b8df0);
    s_ScreenClose = (ScreenCloseFn)(base + 0x02a6908c);
    s_SetRotation = (SetRotationFn)(base + 0x01b1e4f8);
    s_SetValid = (SetValidFn)(base + 0x01b1e514);
    s_DoOutBefore = (DoOutBeforeFn)(base + 0x019ad3f4);
    s_FindPaneByPath = (FindPaneByPathFn)(base + 0x007012ec);
    s_SetString = (SetStringFn)(base + 0x00c74cb4);
    s_SetWheelIcon = (SetWheelIconFn)(base + 0x01acc35c);
    s_SetCheck = (PartSelectionFn)(base + 0x01b1e534);
    s_SelectPart = (PartSelectionFn)(base + 0x01acc214);
    s_UnselectPart = (PartSelectionFn)(base + 0x01acc2b8);
    s_HashName = (HashNameFn)(base + 0x0089011c);
    s_ReleaseDucking = (ReleaseDuckingFn)(base + 0x0108058c);
    s_RequestPause=(PauseRequestFn)(base+0x0102361c);
    s_ReleasePause=(PauseRequestFn)(base+0x00f48498);
    // Install Emote Wheel hooks
    EmoteSoundDelayHook::Install(0x022957d8, 0);
    EmotePauseRequestHook::Install(0x0102361c, 0);
    EmotePauseReleaseHook::Install(0x00f48498, 0);
    PlayerStatusRepeatIconHook::Install(0x00d832c8, 0);
    PlayerCameraInputHook::Install(0x00d17e60, 0);
    PlayerEmoteASUpdateHook::Install(0x0069dbc4, 0);
    ExecutePlayerWhistleCalcHook::Install(0x01d8fee0, 0);
    ExecutePlayerWhistleUpdateHook::Install(0x01d8ffcc, 0);
    UIShortCutMainItemOpenStartHook::Install(0x01b1dc94, 0);
    UIShortCutMainItemUpdateHook::Install(0x01b1e65c, 0);
    UIShortCutMainItemDoOutBeforeHook::Install(0x01b1eef8, 0);
    UIShortCutMainItemCloseEndHook::Install(0x01b1eeb8, 0);
    DpadSelectHook::Install(0x0109db80, 0);

    ConfigFile::Parse(k_DefaultLibrary,k_DefaultWheel,g_Config);
    ApplyWheelConfig();

    WIIXL_LOG("TotK Emotes: All hooks and patches successfully installed!");
}

} // namespace TotK::Emotes

#endif // WIIXL_SWITCH
