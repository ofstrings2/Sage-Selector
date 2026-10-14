#pragma once
#include <nn/fs.hpp>
#include <wiixlaunch/emote_config.hpp>

// These exact exports are present in the game's nnSdk.
namespace nn::fs {
    Result DeleteFile(const char* path);
    Result RenameFile(const char* oldPath,const char* newPath);
}
namespace TotK::Emotes::Storage {
constexpr const char* Library="content:/EmoteConfig/emotes.json";
constexpr const char* Wheel="content:/EmoteConfig/wheel.json";
constexpr const char* Directory="emotesd:/EmoteWheel";
constexpr const char* State="emotesd:/EmoteWheel/last-used.json";
constexpr const char* Backup="emotesd:/EmoteWheel/last-used.json.bak";
constexpr const char* Temp="emotesd:/EmoteWheel/last-used.json.tmp";
inline bool Read(const char* path,char* buffer,size_t capacity) {
    nn::fs::FileHandle file{};
    if(nn::fs::OpenFile(&file,path,nn::fs::OpenMode_Read)!=0)return false;
    long size=0;
    bool ok=nn::fs::GetFileSize(&size,file)==0&&size>0&&uint64_t(size)<capacity;
    if(ok)ok=nn::fs::ReadFile(file,0,buffer,size)==0;
    nn::fs::CloseFile(file);
    if(ok)buffer[size]=0;
    return ok;
}
inline bool Exists(const char* path) {
    nn::fs::FileHandle f{};if(nn::fs::OpenFile(&f,path,nn::fs::OpenMode_Read)!=0)return false;
    nn::fs::CloseFile(f);return true;
}
inline bool Recover() {
    if(Exists(State))return true;
    return Exists(Backup)&&nn::fs::RenameFile(Backup,State)==0;
}
inline bool SaveLast(const ConfigFile::Config& config,const char* id) {
    char previous[256],updated[256];
    if(!ConfigFile::WriteLastUsed(config,id,updated,sizeof(updated)))return false;
    // Already-existing directories are harmless; file operations report real failures.
    nn::fs::CreateDirectory(Directory);
    Recover();
    if(Read(State,previous,sizeof(previous))&&!std::strcmp(previous,updated))return true;
    if(Exists(Temp)&&nn::fs::DeleteFile(Temp)!=0)return false;
    const size_t size=std::strlen(updated);
    if(nn::fs::CreateFile(Temp,size)!=0)return false;
    nn::fs::FileHandle file{};
    if(nn::fs::OpenFile(&file,Temp,nn::fs::OpenMode_Write)!=0)return false;
    const auto flush=nn::fs::WriteOption::CreateOption(nn::fs::WriteOptionFlag_Flush);
    bool ok=nn::fs::WriteFile(file,0,updated,size,flush)==0;
    nn::fs::CloseFile(file);
    if(!ok)return false;
    // Verify the flushed file before replacing the current state.
    char verify[256];
    if(!Read(Temp,verify,sizeof(verify))||std::strcmp(updated,verify))return false;
    if(Exists(Backup)&&nn::fs::DeleteFile(Backup)!=0)return false;
    const bool hadState=Exists(State);
    if(hadState&&nn::fs::RenameFile(State,Backup)!=0)return false;
    if(nn::fs::RenameFile(Temp,State)!=0) {
        if(hadState)nn::fs::RenameFile(Backup,State);
        return false;
    }
    return true;
}
// Recover a complete backup if a previous write was interrupted or damaged.
inline bool LoadLast(const ConfigFile::Config& config,int& last) {
    char text[256];Recover();
    if(Read(State,text,sizeof(text))&&ConfigFile::ParseLastUsed(text,config,last))return true;
    return Read(Backup,text,sizeof(text))&&ConfigFile::ParseLastUsed(text,config,last);
}
} // namespace TotK::Emotes::Storage
