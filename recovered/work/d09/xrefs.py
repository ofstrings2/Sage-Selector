import struct,re,json
from pathlib import Path
b=Path('work/decoded/vanilla.bin').read_bytes()
for s in ['SelectorPlayerSubSchedulerMain','SelectorPlayerSubSchedulerWhistle','ExecutePlayerWhistle','RaumiGolem']:
 ps=[m.start() for m in re.finditer(s.encode()+b'\0',b)];print(s,[hex(x) for x in ps])
 for p in ps:
  refs=[m.start() for m in re.finditer(re.escape(struct.pack('<Q',p)),b)];print(' refs',[hex(x) for x in refs[:30]])
