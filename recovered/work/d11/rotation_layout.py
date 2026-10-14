exec(open('work/resources.py').read().split("f='UI/")[0])
import struct,re
ar=sarc(dec(R/'UI/LayoutArchive/Common.Product.110.Nin_NX_NVN.blarc.zs'));b=ar['blyt/PaIconBtnApp_00.bflyt'];at=struct.unpack_from('<H',b,6)[0]
while at<len(b):
 m=b[at:at+4];n=struct.unpack_from('<I',b,at+4)[0]
 if not n:break
 if m in [b'pan1',b'pic1',b'prt1']:print(m,b[at+12:at+36].split(b'\0')[0],struct.unpack_from('<10f',b,at+36))
 if m in [b'pas1',b'pae1']:print(m)
 at+=n
print(re.findall(rb'[ -~]{5,}',b)[:35])
