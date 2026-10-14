exec(open('work/resources.py').read().split("f='UI/")[0])
O=Path('work/d08');report={}
for rel in ['Pack/Actor/Player.pack.zs','UI/LayoutArchive/Common.Product.110.Nin_NX_NVN.blarc.zs']:
 a=sarc(dec(R/rel));b=sarc(dec(E/rel));report[rel]=[{'path':k,'vanilla':len(a.get(k,b'')),'donor':len(b.get(k,b''))} for k in sorted(a.keys()|b.keys()) if a.get(k)!=b.get(k)]
print(json.dumps(report,indent=2));(O/'resource_diff.json').write_text(json.dumps(report,indent=2))
icons=[p.name for p in (R/'UI/Tex/Icon').iterdir() if any(s in p.name for s in ['SageSoul','Memory','Horse','Warp','Obj_Photo','Obj_Warp'])];print('icons',icons);(O/'icons.json').write_text(json.dumps(icons))
