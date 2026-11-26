import sys,re
def paras(f):
    t=open(f,encoding='utf-8-sig').read().replace('\r\n','\n')
    return [l.strip() for l in t.split('\n') if l.strip()]
def clen(s): return len(re.sub(r'\s+','',s))
for f in sys.argv[1:]:
    p=paras(f); b=p[1:]; tot=sum(clen(x) for x in b)
    print('==',f,tot)
    run=0
    for i,x in enumerate(b):
        l=clen(x)
        if l>=88: print('  LONG',i+1,l,x)
        run=run+1 if l<20 else 0
        if run>=3: print('  RUN',i+1,[clen(y) for y in b[i-2:i+1]],'|'.join(b[i-2:i+1]))
