exec(open('work/d11/render_icons.py').read().split('names=')[0])
for new,n in [('SageMemory','Nt_PauseIconCh_00^s'),('SageHorse','Ds_ShortCutHorseIcon_01^s')]:
 v=Path(f'work/d11/{new}.bntx').read_bytes();p=struct.unpack_from('<Q',v,struct.unpack_from('<Q',v,0x28)[0])[0]
 assert render(v,p).tobytes()==render(b,idx[n]).tobytes()
 np=struct.unpack_from('<Q',v,p+0x60)[0];ln=struct.unpack_from('<H',v,np)[0];assert v[np+2:np+2+ln].decode()==new
 r=struct.unpack_from('<I',v,0x18)[0];assert v[r:r+4]==b'_RLT' and struct.unpack_from('<I',v,r+4)[0]==r
 assert struct.unpack_from('<I',v,0x1c)[0]==len(v)
 print('PASS',new,'native pixels identical; name, file size and relocation header valid')
