from pathlib import Path
s=Path('work/d07/build.py').read_text().replace("W=Path('work/d07')","W=Path('work/d08')")
s=s.replace('mapped:\n','mapped:\nadd x10,x24,#0x3d,lsl #12\nadd x10,x10,#0x6f8\nstlr w1,[x10]\n')
s=s.replace("original=Path('work/decoded/emote.bin').read_bytes()","original=Path('work/d07/d07.bin').read_bytes()")
s=s.replace("source=Path('work/donors/EmoteWheel/exefs/subsdk4').read_bytes()","""# Remove only the two playback-only hook installations. Pause hooks stay.
for at in [0xcbf0,0xccc4]:
 assert struct.unpack_from('<I',raw,at)[0]&0xfc000000==0x94000000
 struct.pack_into('<I',raw,at,0xd2800000) # mov x0, #0; no installed trampoline
# Remove audio-delay hook and animation-update hook bodies, now unregistered.
for a,b in [(0x7770,0x78b0),(0x8ea0,0x90e0)]:raw[a:b]=bytes(b-a)
# Disable emote-only music stop and forced AS reset helpers. Their callers
# in the shared state machine remain, but these helpers now have no side effects.
for a,b in [(0x7f90,0x8050),(0x8180,0x8280)]:
 raw[a:b]=bytes(b-a);struct.pack_into('<I',raw,a,0xd65f03c0)
# Old emote execute body is unreachable after the validated D07 interception.
raw[0x7c78:0x7d5c]=bytes(0x7d5c-0x7c78)
raw[0x7d70:0x7d80]=bytes(0x10)
# Keep config loading, persistence plumbing, pause cleanup and wheel tick.
# Skip only the Down-HUD texture lookup/show-hide loop.
at=0xbe18;to=0xbf04
struct.pack_into('<I',raw,at,0x14000000|(((to-at)//4)&0x3ffffff))
source=Path('work/donors/EmoteWheel/exefs/subsdk4').read_bytes()""")
s=s.replace("'Sage Wheel v0.1 D07 Emote Base';shutil.copytree('work/donors/EmoteWheel',out,dirs_exist_ok=True)","'Sage Wheel v0.2 D08';(out/'exefs').mkdir(parents=True,exist_ok=True);shutil.copy2('work/donors/EmoteWheel/exefs/main.npdm',out/'exefs/main.npdm')")
s=s.replace("(W/'d07.bin')","(W/'d08.bin')")
s=s.replace("assert raw[:0x7c68]==original[:0x7c68] and raw[0x7c78:oldsize]==original[0x7c78:oldsize]", "assert raw[0x8280:0x8ea0]==original[0x8280:0x8ea0] and raw[0x90e0:0x9d80]==original[0x90e0:0x9d80]\nassert raw[0x2000:0x5000]==original[0x2000:0x5000]")
Path('work/d08/build.py').write_text(s)
