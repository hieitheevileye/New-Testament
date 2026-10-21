import pdfplumber, re, sys, json
PDF='/mnt/user-data/uploads/83291_eng.pdf'
def body_chars(pg):
    out=[];caps=[]
    for c in pg.chars:
        if not (0<=c['x0']<432 and c['top']>10): continue
        s=c['size']
        if s>40: caps.append(c); continue
        if 9.8<=s<=10.8: out.append(c)
    return out,caps
def col_lines(chars):
    """group chars into lines; return list of (top,[chars sorted by x0])"""
    chars=sorted(chars,key=lambda c:(round(c['top']),c['x0']))
    lines=[]
    for c in sorted(chars,key=lambda c:c['top']):
        if lines and abs(c['top']-lines[-1][0])<=2.5: lines[-1][1].append(c)
        else: lines.append([c['top'],[c]])
    res=[]
    for top,cs in lines:
        cs.sort(key=lambda c:c['x0'])
        txt='';prev=None;sp=False
        for c in cs:
            if c['text'].isspace(): sp=True; continue
            if prev is not None:
                g=c['x0']-prev['x1']
                if (sp and g>0.5) or g>1.8: txt+=' '
            sp=False
            txt+=c['text'];prev=c
        ital=[('Italic' in c['fontname']) for c in cs if c['text'].strip()]
        res.append(dict(top=top,x0=cs[0]['x0'],text=txt,allital=bool(ital) and all(ital)))
    return res
LASTG=216.5
def gutter(ch):
    cov=[0]*440
    for c in ch:
        for x in range(max(0,int(c['x0'])),min(439,int(c['x1'])+1)): cov[x]+=1
    best=(0,216);run=0
    for x in range(150,300):
        if cov[x]<=3:
            run+=1
            if run>best[0]: best=(run,x-run/2)
        else: run=0
    return best[1]
def page_columns(pg):
    ch,caps=body_chars(pg)
    g=gutter(ch)
    L=[c for c in ch if c['x1']<=g+1]; R=[c for c in ch if c['x0']>g]
    return col_lines(L),col_lines(R),caps,g
if __name__=='__main__':
    pdf=pdfplumber.open(PDF)
    for pn in map(int,sys.argv[1:]):
        l,r,caps,g=page_columns(pdf.pages[pn])
        print('=== page',pn,'caps',[(c['text'],round(c['x0']),round(c['top'])) for c in caps])
        for name,col in (('L',l),('R',r)):
            for ln in col: print(name,round(ln['top']),round(ln['x0']),'I' if ln['allital'] else ' ',repr(ln['text']))
