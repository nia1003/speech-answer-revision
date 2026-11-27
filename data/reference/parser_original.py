import json,re,sys,random
from collections import Counter
NUM=re.compile(r'(?<![\w.])\d+(?:,\d{3})*(?:\.\d+)?')
def val(s):
    return float(s.replace(',',''))
def parse(item):
    q=item['question']; a=item['answer']
    qn=set(val(x) for x in NUM.findall(q))
    steps=[]
    for m in re.finditer(r'<<([^<>]*?)=([^<>=]*)>>',a):
        expr,res=m.group(1),m.group(2)
        try: r=float(res.replace(',',''))
        except: r=None
        toks=[val(x) for x in NUM.findall(expr)]
        steps.append((expr,r,toks))
    depth=[];deps=[];amb=False
    for i,(expr,r,toks) in enumerate(steps):
        d=[];
        for t in toks:
            js=[j for j in range(i) if steps[j][1] is not None and abs(steps[j][1]-t)<1e-9]
            if js:
                j=js[-1]; d.append(j)
                if t in qn: amb=True
        deps.append(sorted(set(d)))
        depth.append(1+max([depth[j] for j in d],default=0))
    return steps,deps,(max(depth) if depth else 0),amb
if __name__=='__main__':
    data=[json.loads(l) for l in open(sys.argv[1])]
    D=Counter();S=Counter();A=0
    for it in data:
        st,dp,d,amb=parse(it); D[d]+=1;S[len(st)]+=1;A+=amb
    print('depth',sorted(D.items()));print('steps',sorted(S.items()));print('amb',A)
