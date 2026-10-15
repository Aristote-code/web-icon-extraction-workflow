import pathlib,json,hashlib,re,copy,collections,csv,html,zipfile,shutil,gzip,argparse
import xml.etree.ElementTree as E
parser=argparse.ArgumentParser(description='Normalize and deduplicate browser SVG captures')
parser.add_argument('--input',type=pathlib.Path,required=True)
parser.add_argument('--output',type=pathlib.Path,required=True)
args=parser.parse_args()
DATA=args.input.resolve();OUT=args.output.resolve()
if OUT==DATA or DATA.is_relative_to(OUT):raise SystemExit('Output must not contain input data')
for d in ['svg','originals','raw-symbols','raw-inline']:
    if (OUT/d).exists():shutil.rmtree(OUT/d)
for d in ['svg','originals','raw-symbols','raw-inline','evidence']: (OUT/d).mkdir(parents=True,exist_ok=True)
NS='http://www.w3.org/2000/svg'; XL='http://www.w3.org/1999/xlink'
E.register_namespace('',NS); E.register_namespace('xlink',XL)
paths=sorted([*(DATA/'captures').glob('*.json'),*(DATA/'captures').glob('*.json.gz')],key=lambda p:int(p.name.split('.')[0]))
if not paths:raise SystemExit('No captures found')
captures=[json.loads(gzip.open(p,'rt').read() if p.suffix=='.gz' else p.read_text()) for p in paths]
assets={}; originals={}; failures={}; parse_errors=[]; source_symbols=[]
def sha(b): return hashlib.sha256(b).hexdigest()
def local(t):return t.split('}')[-1]
def parse(s):
    s=re.sub(r'\s_ng(?:content|host)-[^=\s]+="[^"]*"','',s)
    if 'xlink:' in s and 'xmlns:xlink' not in s:s=s.replace('>',' xmlns:xlink="'+XL+'">',1)
    return E.fromstring(s)
def clean(e):
    for n in e.iter():
        if not n.tag.startswith('{'):n.tag='{'+NS+'}'+n.tag
        for a in list(n.attrib):
            if a.startswith('_ng') or a in ['class','data-test','aria-hidden','focusable','role','tabindex','aria-label'] or a.startswith('data-'):del n.attrib[a]
        if n.get('style') in ['color: inherit;','color: inherit']:del n.attrib['style']
        for a,v in list(n.attrib.items()):
            while 'var(' in v:
                nv=re.sub(r'var\([^(),]+,\s*([^()]+)\)',r'\1',v)
                if nv==v:break
                v=nv
            n.set(a,v)
        n.attrib=dict(sorted(n.attrib.items()))
    return e
def refs(e):
    r=set()
    for n in e.iter():
        for k,v in n.attrib.items():
            r.update(re.findall(r'url\([\"\']?#([^\)\"\']+)',v))
            if local(k)=='href' and v.startswith('#'):r.add(v[1:])
    return r
def standalone(e,index):
    e=copy.deepcopy(e)
    if local(e.tag)=='symbol':
        e.tag='{'+NS+'}svg';e.attrib.pop('id',None)
    e.attrib.pop('width',None);e.attrib.pop('height',None)
    if not e.get('viewBox'):e.set('viewBox','0 0 24 24')
    internal={n.get('id') for n in e.iter() if n.get('id')}; needed=refs(e)-internal; added=set(); defs=E.Element('{'+NS+'}defs')
    while needed:
        id=needed.pop()
        if id in added:continue
        if id in index:
            node=copy.deepcopy(index[id]);defs.append(node);added.add(id);needed|=refs(node)-internal-added
    if len(defs):e.insert(0,defs)
    return clean(e)
def add(e,name,kind,provenance,index,raw=None):
    e=standalone(e,index)
    if not any(local(n.tag) in ['path','circle','rect','polygon','ellipse','line','polyline','image','text','use'] for n in e.iter()):return
    unresolved=sorted(refs(e)-{n.get('id') for n in e.iter() if n.get('id')})
    b=E.tostring(e,encoding='utf-8'); h=sha(b)
    if h not in assets:
        safe=re.sub('[^a-zA-Z0-9_-]+','-',name).strip('-')[:100] or 'icon'
        file='svg/'+safe+'-'+h[:10]+'.svg';(OUT/file).write_bytes(b)
        rawfile=None
        if raw:
            rawfile=('raw-symbols/' if kind.endswith('symbol') else 'raw-inline/')+h+'.xml';(OUT/rawfile).write_text(raw)
        assets[h]={'sha256':h,'file':file,'name':name,'kinds':[],'sources':[],'raw':rawfile,'unresolvedReferences':unresolved,'verification':'extracted from browser DOM or downloaded sprite; XML parsed; local reference closure checked'}
    a=assets[h]
    if kind not in a['kinds']:a['kinds'].append(kind)
    if provenance not in a['sources']:a['sources'].append(provenance)
for i,c in enumerate(captures):
    provenance={'pageUrl':c['dom']['url'],'state':c['label'],'capture':i}
    for a in c['bundle']['assets']:
        if not a['url'].startswith('http') or a['kind']!='image':continue
        p=pathlib.Path(a['path']);p=p if p.is_absolute() else DATA/p;b=p.read_bytes();h=sha(b)
        if h not in originals:
            safe=re.sub('[^a-zA-Z0-9._-]+','-',a['name'].split('#')[0])[:120];dest='originals/'+h[:10]+'-'+safe;(OUT/dest).write_bytes(b)
            originals[h]={'file':dest,'sha256':h,'contentType':a['contentType'],'urls':[],'pages':[],'bytes':len(b)}
        o=originals[h]
        if a['url'] not in o['urls']:o['urls'].append(a['url'])
        if c['dom']['url'] not in o['pages']:o['pages'].append(c['dom']['url'])
    for a in c['bundle']['failures']:
        key=a['url'];failures.setdefault(key,{'url':key,'reasons':[],'states':[]})
        if a['reason'] not in failures[key]['reasons']:failures[key]['reasons'].append(a['reason'])
        if c['label'] not in failures[key]['states']:failures[key]['states'].append(c['label'])
    nodes=[]
    for s in c['dom']['symbols']:
        try:nodes.append((s,parse(s)))
        except Exception as ex:parse_errors.append(str(ex))
    index={n.get('id'):n for _,e in nodes for n in e.iter() if n.get('id')}
    for wrapper in c['dom']['svgs']:
        try:
            for n in parse(wrapper).iter():
                if n.get('id'):index[n.get('id')]=n
        except Exception:pass
    for s,e in nodes:
        add(e,e.get('id','symbol'),'dom-symbol',dict(provenance,symbolId=e.get('id')),index,s)
    for s in c['dom']['svgs']:
        try:
            e=parse(s)
            if any(local(n.tag)=='symbol' for n in e.iter()):continue
            if any(local(n.tag)=='use' for n in e.iter()):continue
            kind='picker-pictogram' if 'custom-icon' in s else 'inline-svg'
            name=kind+'-'+sha(E.tostring(clean(copy.deepcopy(e))))[:10]
            add(e,name,kind,provenance,index,s)
        except Exception as ex:parse_errors.append(str(ex))
# Split every symbol in successfully downloaded original SVG sprite files.
for o in originals.values():
    if o['contentType']!='image/svg+xml':continue
    try:e=E.parse(OUT/o['file']).getroot()
    except Exception:continue
    index={n.get('id'):n for n in e.iter() if n.get('id')}
    syms=[n for n in e.iter() if local(n.tag)=='symbol']
    o['symbolCount']=len(syms)
    for n in syms:
        source_symbols.append(n.get('id'))
        add(n,n.get('id','symbol'),'original-sprite-symbol',{'assetUrl':o['urls'][0].split('#')[0],'originalFile':o['file'],'symbolId':n.get('id'),'usage':'present in downloaded sprite; on-screen use not assumed'},index,E.tostring(n,encoding='unicode'))
M={'date':'2026-10-15','timezone':'Africa/Kigali','entryUrl':captures[0]['dom']['url'],'assets':list(assets.values()),'originalFiles':list(originals.values()),'parseErrors':parse_errors,'deduplication':'SHA-256 of normalized standalone SVG; strip framework attributes and presentation classes; retain geometry/viewBox/colors/IDs needed by defs. Exact byte deduplication for downloaded originals. Not perceptual equivalence.'}
(OUT/'manifest.json').write_text(json.dumps(M,indent=2))
with (OUT/'manifest.csv').open('w') as f:
    w=csv.writer(f);w.writerow(['file','name','kinds','sha256','source_count','unresolved_references'])
    for a in assets.values():w.writerow([a['file'],a['name'],';'.join(a['kinds']),a['sha256'],len(a['sources']),';'.join(a['unresolvedReferences'])])
(OUT/'download-failures.json').write_text(json.dumps(list(failures.values()),indent=2))
coverage=[]
for i,c in enumerate(captures):
    status='loading shell only' if i in [7,8,9,10] else 'rendered state captured'
    statepath=DATA/f'state-{i}.txt'
    if statepath.exists() and ('image Loading...' in statepath.read_text() or 'v4-loader' in statepath.read_text()):status='partial/loading at capture; see limitations'
    coverage.append({'capture':i,'state':c['label'] if i!=31 else 'List breadcrumb menu','url':c['dom']['url'],'status':status,'inlineSvgCount':len(c['dom']['svgs']),'domSymbolCount':len(c['dom']['symbols'])})
(OUT/'coverage.json').write_text(json.dumps(coverage,indent=2))
stats={'standaloneSvgs':len(assets),'originalSpriteSymbols':len(source_symbols),'pickerPictograms':sum('picker-pictogram' in a['kinds'] for a in assets.values()),'domSymbols':sum('dom-symbol' in a['kinds'] for a in assets.values()),'originalFiles':len(originals),'captures':len(captures),'uniqueUrls':len(set(c['dom']['url'] for c in captures)),'unresolvedSvgReferences':sum(bool(a['unresolvedReferences']) for a in assets.values()),'parseErrors':len(parse_errors)}
(OUT/'summary.json').write_text(json.dumps(stats,indent=2))
cards=[]
for a in sorted(assets.values(),key=lambda a:a['name']):
    if a['unresolvedReferences']:continue
    cards.append('<a class="card" download href="'+a['file']+'" data-name="'+html.escape(a['name'].lower()+' '+' '.join(a['kinds']),quote=True)+'"><img loading="lazy" src="'+a['file']+'"><span>'+html.escape(a['name'])+'</span><small>'+html.escape(', '.join(a['kinds']))+'</small></a>')
gallery='''<!doctype html><html><meta charset="utf-8"><title>ClickUp extracted icons</title><style>body{font:15px system-ui;margin:32px;background:#f5f5fa;color:#252139}h1{margin-bottom:8px}input{width:min(600px,90%);padding:14px;border:1px solid #ccc;border-radius:8px;margin:20px 0}main{display:grid;grid-template-columns:repeat(auto-fill,minmax(155px,1fr));gap:12px}.card{background:white;border:1px solid #e4e2ed;padding:18px;display:flex;flex-direction:column;align-items:center;gap:16px;text-decoration:none;color:inherit;border-radius:10px;overflow:hidden}.card img{width:46px;height:46px}.card span{font-size:11px;overflow-wrap:anywhere;text-align:center}.card small{font-size:10px;color:#777}.card:hover{border-color:#7659df}header{position:sticky;top:0;background:#f5f5fa;z-index:1}p{max-width:900px}</style><header><h1>ClickUp icons & pictograms</h1><p>ACTUAL EXTRACTION · 15 October 2026 · '''+str(len(assets))+''' standalone SVGs. Click an icon to download. Originals and provenance are in the package. Sprite presence does not imply verified screen usage.</p><input id="q" placeholder="Search icon names or source type…"><span id="count"></span></header><main>'''+''.join(cards)+'''</main><script>q.oninput=()=>{let n=0;document.querySelectorAll('.card').forEach(e=>{e.hidden=!e.dataset.name.includes(q.value.toLowerCase());e.style.display=e.hidden?'none':'flex';if(!e.hidden)n++});count.textContent=n+' matches'}</script></html>'''
(OUT/'gallery.html').write_text(gallery)
print(json.dumps(stats,indent=2))
