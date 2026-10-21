import pdfplumber, re, json, collections, sys
from lines import page_columns, PDF
ORDER=[('MAT',28,1071),('MRK',16,678),('LUK',24,1151),('JHN',21,879),('ACT',28,1007),('ROM',16,433),('1CO',16,437),('2CO',13,257),('GAL',6,149),('EPH',6,155),('PHP',4,104),('COL',4,95),('1TH',5,89),('2TH',3,47),('1TI',6,113),('2TI',4,83),('TIT',3,46),('PHM',1,25),('HEB',13,303),('JAS',5,108),('1PE',5,105),('2PE',3,61),('1JN',5,105),('2JN',1,13),('3JN',1,14),('JUD',1,25),('REV',22,404)]
MARK='\u2063'
def parse(start=5):
    pdf=pdfplumber.open(PDF)
    V=collections.OrderedDict(); log=[]
    bi=-1;ch=None;vn=None;insum=False;done=False
    def add(key,line):
        t=V.get(key,'')
        if not t: V[key]=line;return
        if t.endswith('\xad'): V[key]=t[:-1]+MARK+line
        elif t.endswith('-') and len(t)>1 and t[-2].isalpha(): V[key]=t[:-1]+MARK+line
        else: V[key]=t+' '+line
    for pn in range(start,len(pdf.pages)):
        pg=pdf.pages[pn]
        L,R,caps,g=page_columns(pg)
        tt=[c for c in pg.chars if 13<=c['size']<=30 and 'Centaur' in c['fontname'] and c['top']>0]
        LL=[('L',x) for x in L];RR=[('R',x) for x in R]
        if tt:
            bd=min(c['top'] for c in tt)-1
            lo=min(c['x0'] for c in tt);hi=max(c['x1'] for c in tt)
            Z=lambda lst,z:[(c,l,z) for c,l in lst if (l['top']>=bd)==bool(z)]
            if lo<g<hi: seq=Z(LL,0)+Z(RR,0)+Z(LL,1)+Z(RR,1)
            elif hi<=g: seq=Z(LL,0)+Z(LL,1)+[(c,l,1) for c,l in RR]
            else: seq=[(c,l,0) for c,l in LL]+Z(RR,0)+Z(RR,1)
        else:
            seq=[(c,l,0) for c,l in LL+RR]
        capmap={}
        for cp in caps:
            colc='L' if cp['x0']<g else 'R'
            cand=[l for c2,l,z in seq if c2==colc and -6<=l['top']-cp['top']<=14]
            if cand: capmap[id(min(cand,key=lambda l:abs(l['top']-cp['top'])))]=cp['text']
            else: log.append(f'p{pn} unmatched dropcap {cp["text"]!r} at {round(cp["top"])}')
        newbook=bool(tt)
        for col,ln,zone in seq:
            t=ln['text'].replace('¶','').strip()
            if not t: continue
            if t.strip()=='THE END': continue
            if (21<=ln['top']<=25 and not re.search(r'[a-z]',t)) or re.match(r'^\d{3,4}$',t) or (ln['top']<30 and re.search(r'\d+:\d+',t)): continue
            if id(ln) in capmap:
                mm=re.match(r'^(\d{1,3}\s+)?(\S+)(.*)$',t)
                t=(mm.group(1) or '')+capmap[id(ln)]+mm.group(2).lower()+mm.group(3)
            if newbook and zone==1:
                bi+=1;ch=1;vn=0;insum=True;newbook=False
            m=re.match(r'^CHAPTER\s+(\d+)$',t,re.I)
            if m: ch=int(m.group(1));vn=0;insum=True;continue
            if insum:
                if ln['allital']: continue
                insum=False;vn=1
                add((bi,ch,vn),t);continue
            m=re.match(r'^(\d{1,3})\s+(.*)$',t) or re.match(r'^(\d{1,3})$',t)
            if m:
                n=int(m.group(1))
                if n!=vn+1: log.append(f'p{pn} jump {ch}:{vn}->{n} {t[:40]!r}')
                vn=n; add((bi,ch,vn),m.group(2) if m.lastindex==2 else ''); continue
            if vn==0: log.append(f'p{pn} orphan {t[:50]!r}');continue
            add((bi,ch,vn),t)
        if bi==26 and ch==22 and vn==21: done=True;break
    return V,log,pn
def resolve(V):
    vocab=set()
    V={k:re.sub('\xad(?=[A-Za-z])','-',t) if False else t for k,t in V.items()}
    for t in V.values():
        for w in re.findall(r"[A-Za-zÆæ’']+(?:-[A-Za-zÆæ’']+)*",t.replace(MARK,' ')): vocab.add(w.lower())
    unres=[]
    def fix(key,t):
        def rep(m):
            l,r=m.group(1),m.group(2)
            j=(l+r).lower();h=(l+'-'+r).lower()
            if j in vocab: return l+r
            if h in vocab: return l+'-'+r
            unres.append((key,l,r)); return l+r
        return re.sub(r"([A-Za-zÆæ’']+)"+MARK+r"([A-Za-zÆæ’']+)",rep,t)
    out={}
    for k,t in V.items():
        t=fix(k,t).replace(MARK,'')
        t=re.sub(r'\s+',' ',t).strip(); out[k]=t
    return out,unres
if __name__=='__main__':
    V,log,last=parse()
    out,unres=resolve(V)
    json.dump({f'{k[0]}|{k[1]}|{k[2]}':v for k,v in out.items()},open('raw.json','w'),ensure_ascii=False)
    print('last page',last,'verses',len(out)); print('log',len(log)); print('\n'.join(log[:40]))
    print('unresolved hyphens',len(unres),unres[:30])
