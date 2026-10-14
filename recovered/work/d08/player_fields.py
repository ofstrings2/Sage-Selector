exec(open('work/resources.py').read().split("f='UI/")[0])
import struct

def byml(b):
 assert b[:2]==b'YB';u=lambda o:struct.unpack_from('<I',b,o)[0];n=lambda o:int.from_bytes(b[o:o+3],'little')
 def table(o):return [b[o+u(o+4+i*4):].split(b'\0')[0].decode() for i in range(n(o+1))] if o else []
 keys=table(u(4));strings=table(u(8))
 def value(t,v):
  if t==0xa0:return strings[v]
  if t==0xd0:return bool(v)
  if t==0xd1:return struct.unpack('<i',struct.pack('<I',v))[0]
  if t==0xd2:return struct.unpack('<f',struct.pack('<I',v))[0]
  if t==0xd3:return v
  if t==0xff:return None
  if t==0xc1:return {keys[n(v+4+i*8)]:value(b[v+7+i*8],u(v+8+i*8)) for i in range(n(v+1))}
  if t==0xc0:
   count=n(v+1);base=(v+4+count+3)&~3
   return [value(b[v+4+i],u(base+i*4)) for i in range(count)]
  return {'type':hex(t),'value':v}
 return value(b[u(12)],u(12))
a=sarc(dec(R/'Pack/Actor/Player.pack.zs'));b=sarc(dec(E/'Pack/Actor/Player.pack.zs'));diff=[]
def walk(a,b,path):
 if a==b:return
 if isinstance(a,dict) and isinstance(b,dict):
  for k in sorted(a.keys()|b.keys()):walk(a.get(k),b.get(k),path+'/'+k)
 else:diff.append({'field':path,'vanilla':a,'donor':b})
for k in a:
 if a[k]!=b.get(k):walk(byml(a[k]),byml(b[k]),k)
print(json.dumps(diff,indent=2));Path('work/d08/player_field_diff.json').write_text(json.dumps(diff,indent=2))
