#!/usr/bin/env python3
"""data/nt-plain.json + data/jesus-words.txt -> www/nt.json (red letters marked with U+27E6/U+27E7).
Fails (exit 1) if any listed verse or phrase cannot be found."""
import json, re, sys, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORDER=['MAT','MRK','LUK','JHN','ACT','ROM','1CO','2CO','GAL','EPH','PHP','COL','1TH','2TH','1TI','2TI','TIT','PHM','HEB','JAS','1PE','2PE','1JN','2JN','3JN','JUD','REV']
VERB=r'(?:said|saith|saying|say|spake|speak|answered|answereth|answering|asked|cried|crying|called|charged|commanded|replied|prayed|told)'
def trim_intro(s):
    m=re.match(r'.{0,170}?\b'+VERB+r'\b[^,:;]{0,70}?[,:;]\s*',s,re.S|re.I)
    if not m: return None
    pos=m.end()
    while True:
        m2=re.match(r'(?:saying\b|(?:(?:and|then)\s+)?(?:he|they)\s+(?:said|saith|spake|answered|asked|called)\b|(?:and|then)\s+(?:said|saith|spake|answered|asked|called)\b)[^,:;]{0,50}?[,:;]\s*',s[pos:],re.I)
        if not m2: break
        pos+=m2.end()
    return pos
def main():
    nt=json.load(open(os.path.join(ROOT,'data/nt-plain.json')))
    idx={c:{(ci+1,n):(ci,i) for ci,ch in enumerate(nt[c]) for i,(n,_) in enumerate(ch)} for c in ORDER}
    spans={}; errs=[]; warns=[]
    for line in open(os.path.join(ROOT,'data/jesus-words.txt'),encoding='utf-8'):
        line=line.strip()
        if not line or line.startswith('#'): continue
        book,rest=line.split(' ',1)
        for tok in rest.split(' ; '):
            tok=tok.strip()
            m=re.fullmatch(r'(\d+):(\d+)(\^)?(?:-(\d+))?(?:~([^|]*))?(?:\|(.*))?',tok)
            if not m: errs.append(f'{book} bad token {tok!r}'); continue
            ch,v1,hat,v2,start,stop=m.groups(); ch=int(ch); v1=int(v1); v2=int(v2) if v2 else v1
            for v in range(v1,v2+1):
                if (ch,v) not in idx[book]: errs.append(f'{book} {ch}:{v} does not exist'); continue
                ci,i=idx[book][(ch,v)]; s=nt[book][ci][i][1]; a=0; b=len(s)
                if v==v1:
                    if hat:
                        p=trim_intro(s)
                        if p is None: errs.append(f'{book} {ch}:{v} no intro found for ^')
                        else:
                            a=p
                            if not s[a:a+1].isupper(): warns.append(f'{book} {ch}:{v} red starts {s[a:a+14]!r} after {s[max(0,a-30):a]!r}')
                            if a>110: warns.append(f'{book} {ch}:{v} long intro {s[:a]!r}')
                    if start is not None:
                        k=s.find(start)
                        if k<0: errs.append(f'{book} {ch}:{v} start phrase {start!r} not found')
                        else: a=k+len(start)
                if v==v2 and stop is not None:
                    k=s.find(stop,a)
                    if k<0: errs.append(f'{book} {ch}:{v} end phrase {stop!r} not found')
                    else: b=k
                while a<b and s[a] in ' ;,:': a+=1
                while b>a and s[b-1]==' ': b-=1
                if a<b: spans.setdefault((book,ch,v),[]).append((a,b))
                else: errs.append(f'{book} {ch}:{v} empty red span')
    out={}; red=0; reds={}
    for c in ORDER:
        out[c]=[]
        for ci,ch in enumerate(nt[c]):
            row=[]
            for n,s in ch:
                sp=sorted(spans.get((c,ci+1,n),[]))
                if sp:
                    merged=[]
                    for a,b in sp:
                        if merged and a<=merged[-1][1]: merged[-1][1]=max(merged[-1][1],b)
                        else: merged.append([a,b])
                    t='';last=0
                    for a,b in merged: t+=s[last:a]+'⟦'+s[a:b]+'⟧'; last=b
                    s=t+s[last:]; red+=1; reds[c]=reds.get(c,0)+1
                row.append([n,s])
            out[c].append(row)
    for w in warns: print('WARN',w)
    if errs:
        print('ERRORS:'); print('\n'.join(errs)); sys.exit(1)
    total=sum(len(ch) for b in out.values() for ch in b)
    assert total==7957, total
    os.makedirs(os.path.join(ROOT,'www'),exist_ok=True)
    json.dump(out,open(os.path.join(ROOT,'www/nt.json'),'w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
    print(f'OK: {total} verses, {red} with red letters', reds)
main()
