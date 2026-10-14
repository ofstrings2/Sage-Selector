exec(open('work/resources.py').read().split("f='UI/")[0])
import byml
for folder in ['Event/EventSetting','Event/EventFlow']:
 for p in (R/folder).glob('*GanonWakeUp*'):
  print(p)
  if p.suffix=='.bgyml':print(byml.Byml(p.read_bytes()).parse())
