import re,sys
def clen(s): return len(re.sub(r'\s+','',s))
def autosplit(f,limit=84):
    t=open(f,encoding='utf-8-sig').read().replace('\r\n','\n')
    lines=t.split('\n'); out=[]
    for ln in lines:
        s=ln.strip()
        if clen(s)>=limit and not s.startswith('第0'):
            # split at sentence ends outside quotes
            parts=[];buf='';depth=0
            for ch in s:
                buf+=ch
                if ch in '“「': depth+=1
                if ch in '”」': depth=max(0,depth-1)
                if ch in '。！？' and depth==0:
                    parts.append(buf);buf=''
            if buf: parts.append(buf)
            if len(parts)>=2:
                # choose split index nearest middle with both sides>=15
                tot=sum(len(x) for x in parts);best=None;acc=0
                for i in range(1,len(parts)):
                    acc+=len(parts[i-1])
                    if acc>=8 and tot-acc>=8:
                        d=abs(acc-tot/2)
                        if best is None or d<best[0]: best=(d,i)
                if best:
                    i=best[1]; a=''.join(parts[:i]); b=''.join(parts[i:])
                    out.append(a); out.append(''); out.append(b); continue
        out.append(ln)
    open(f,'w',encoding='utf-8').write('\n'.join(out))
def patch(f,old,new):
    t=open(f,encoding='utf-8').read()
    assert old in t,(f,old[:20])
    open(f,'w',encoding='utf-8').write(t.replace(old,new,1))
if __name__=='__main__':
    for f in sys.argv[1:]: autosplit(f)

def commasplit(f,limit=92):
    t=open(f,encoding='utf-8').read().split('\n'); out=[]
    for ln in t:
        s=ln.strip()
        if clen(s)>=limit and not s.startswith('第0'):
            depth=0;cands=[]
            for i,ch in enumerate(s):
                if ch in '“「': depth+=1
                if ch in '”」': depth=max(0,depth-1)
                if ch in '，：' and depth==0 and 20<=i<=len(s)-20: cands.append(i+1)
            if cands:
                k=min(cands,key=lambda x:abs(x-len(s)/2)); out.append(s[:k]); out.append(''); out.append(s[k:]); continue
        out.append(ln)
    open(f,'w',encoding='utf-8').write('\n'.join(out))

def quotesplit(f,limit=92):
    t=open(f,encoding='utf-8').read().split('\n'); out=[]
    for ln in t:
        s=ln.strip()
        if clen(s)>=limit and not s.startswith('第0'):
            depth=0;cands=[]
            for i,ch in enumerate(s):
                if ch in '“「': depth+=1
                if ch in '”」': depth=max(0,depth-1)
                if ch in '。！？' and 20<=i<=len(s)-20 and s[i+1:i+2] not in '”」': cands.append((i+1,depth))
            if cands:
                k,d=min(cands,key=lambda x:abs(x[0]-len(s)/2))
                a=s[:k]; b=s[k:]
                if d>0: b='“'+b
                out.append(a); out.append(''); out.append(b); continue
        out.append(ln)
    open(f,'w',encoding='utf-8').write('\n'.join(out))
def ap(f,anchor,new,before=False):
    t=open(f,encoding='utf-8').read(); assert anchor in t,(f,anchor[:15])
    r=(new+"\n\n"+anchor) if before else (anchor+"\n\n"+new)
    open(f,'w',encoding='utf-8').write(t.replace(anchor,r,1))
def fixall(files):
    for g in files: autosplit(g); commasplit(g); quotesplit(g)

def mergeruns(f):
    t=open(f,encoding='utf-8').read().split('\n')
    title=t[0]; ps=[x.strip() for x in t[1:] if x.strip()]
    changed=True
    while changed:
        changed=False
        for i in range(2,len(ps)):
            if clen(ps[i])<20 and clen(ps[i-1])<20 and clen(ps[i-2])<20:
                if not ps[i-1].startswith('“'):
                    ps[i-2]=ps[i-2]+ps[i-1]; del ps[i-1]
                elif not ps[i].startswith('“'):
                    ps[i-1]=ps[i-1]+ps[i]; del ps[i]
                else:
                    ps[i-1]=ps[i-1]+ps[i]; del ps[i]
                changed=True;break
    open(f,'w',encoding='utf-8').write(title+'\n\n'+'\n\n'.join(ps)+'\n')
def delpara(f,start):
    t=open(f,encoding='utf-8').read().split('\n'); out=[];skip=False
    for i,l in enumerate(t):
        if l.strip().startswith(start) : continue
        out.append(l)
    open(f,'w',encoding='utf-8').write('\n'.join(out))
