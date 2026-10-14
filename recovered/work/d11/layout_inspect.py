exec(open('work/resources.py').read().split("f='UI/")[0])
import struct,re
ar=sarc(dec(R/'UI/LayoutArchive/Common.Product.110.Nin_NX_NVN.blarc.zs'))
for k in ['blyt/PaChallengeLogTabBtn_00.bflyt','blyt/PaMemoryListBtn_00.bflyt']:
 b=ar[k];Path('work/d11/'+k.split('/')[-1]).write_bytes(b);print(k);print(re.findall(rb'[ -~]{5,}',b));print('utf16',b.decode('utf-16le',errors='replace')[:200])
