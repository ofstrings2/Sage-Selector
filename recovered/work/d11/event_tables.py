exec(open('work/resources.py').read().split("f='UI/")[0])
import byml
for n in ['EventSetting','GameEventBaseSetting','GameEventMetadata']:
 v=byml.Byml(dec(R/f'RSDB/{n}.Product.121.rstbl.byml.zs')).parse()
 if isinstance(v,list):r=[x for x in v if 'GanonWakeUp' in str(x)]
 else:r={k:x for k,x in v.items() if 'GanonWakeUp' in str(x) or 'GanonWakeUp' in k}
 print(n,r);Path('work/d11/'+n+'.json').write_text(json.dumps(r,indent=2))
