import json,re
from parse import parse,resolve,ORDER
V,log,last=parse(); out,unres=resolve(V)
assert not log,log
FIX={'Stephan as':'Stephanas','things THE saith':'things saith'}
plain={}
for (b,c,v),t in out.items():
    t=t.replace('\xad','-')
    t=re.sub(r'\s+([,.;:?!])',r'\1',t); t=re.sub(r'\(\s+','(',t); t=re.sub(r'\s+\)',')',t)
    for a,z in FIX.items(): t=t.replace(a,z)
    if (b,c,v)==(26,22,21): t=re.sub(r'\s*END$','',t)
    t=re.sub(r'\s+',' ',t).strip()
    plain.setdefault(ORDER[b][0],{}).setdefault(c,[]).append([v,t])
nt={code:[plain[code][c] for c in sorted(plain[code])] for code,_,_ in ORDER}
json.dump(nt,open('nt-plain.json','w'),ensure_ascii=False,separators=(',',':'))
print('verses',sum(len(ch) for b in nt.values() for ch in b))
chk={('JHN',3,16),('MAT',5,3),('ROM',8,28),('JHN',14,6),('REV',22,21),('MAT',28,20),('1CO',13,4),('HEB',11,1),('JUD',1,25),('PHM',1,25),('3JN',1,14),('2JN',1,13),('ACT',1,1),('LUK',2,1),('REV',1,1),('GAL',1,1),('JHN',11,35)}
for code,c,v in sorted(chk):
    print(code,c,v,[t for n,t in nt[code][c-1] if n==v][0])
print([ (k,t) for k,t in [(f'{b}',x) for b in ()]])
print('hyphen-kept:',sorted({w for b in nt.values() for ch in b for n,t in ch for w in re.findall(r"[A-Za-z’]+-[A-Za-z’]+",t)}))
print('GOD-ward check',[ (code,c,n) for code,b in nt.items() for c,ch in enumerate(b,1) for n,t in ch if 'ward' in t and 'God' in t and '-' in t][:5])
