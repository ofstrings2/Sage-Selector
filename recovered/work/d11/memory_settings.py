exec(open('work/resources.py').read().split("f='UI/")[0])
import byml
p=R/'Event/EventSetting/EventSettingComponentList/DmT_OP_GanonWakeUp_PreRender_Memory.engine__event__EventSettingComponentList.bgyml'
v=byml.Byml(p.read_bytes()).parse();print(v)
for s in v.values():
 if isinstance(s,str) and s.startswith('Work/'):
  q=R/(s[5:].removesuffix('.gyml')+'.bgyml')
  if q.exists():print(str(q.relative_to(R)),byml.Byml(q.read_bytes()).parse())
