exec(open('work/resources.py').read().split("f='UI/")[0])
import struct,re
ar=sarc(dec(R/'UI/LayoutArchive/Common.Product.110.Nin_NX_NVN.blarc.zs'))
for k in ['blyt/PaChallengeLogTabBtn_00.bflyt','blyt/PaMemoryListBtn_00.bflyt']:
 b=ar[k];Path('work/d11/'+k.split('/')[-1]).write_bytes(b);print(k);print(re.findall(rb'[ -~]{5,}',b))
 at=struct.unpack_from('<H',b,6)[0]
 while at<len(b):
  magic=b[at:at+4];size=struct.unpack_from('<I',b,at+4)[0]
  if not size:break
  if magic==b'txt1':print('TEXT',hex(at),b[at:at+size].hex())
  at+=size
