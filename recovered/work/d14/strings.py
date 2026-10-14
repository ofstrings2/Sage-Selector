from pathlib import Path
import re
b=Path('work/decoded/vanilla.bin').read_bytes()
for m in re.finditer(rb'[ -~]{5,}\x00',b):
 s=m.group()[:-1].decode()
 if any(v in s.lower() for v in ['warp','equipment']) and len(s)<140:print(hex(m.start()),s)
