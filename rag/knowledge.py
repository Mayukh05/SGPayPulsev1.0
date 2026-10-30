"""Versioned indexing and deterministic name-aware retrieval of curated JSON."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

ALIASES={"lee hsien loong":["senior minister lee","sm lee","hsien loong","lee hsien"],
         "jasmin lau":["jasmine lau","jasmin","jasmine"]}

def normalized(s):
    return re.sub(r"[^a-z0-9 ]+"," ",s.casefold()).strip()

def structured_entries(base:Path):
    data=base/'data'
    people=json.loads((data/'mp_ministers_data.json').read_text(encoding='utf-8'))
    framework=json.loads((data/'remuneration_framework_2026.json').read_text(encoding='utf-8'))
    entries=[]
    for name,person in people.items():
        lines=[f"Person: {name}",f"Current appointment: {person.get('current_appointment','Unknown')}",
               f"Constituency: {person.get('constituency','Unknown')}",
               f"Biography: {person.get('biography_summary','')}",
               f"Parliamentary terms: {', '.join(map(str,person.get('parliamentary_terms',[]))) or 'Not recorded'}",
               f"Historical coverage: {person.get('historical_coverage','Unspecified')}",
               "Individual actual salary: Not publicly verified in this dataset."]
        for h in person.get('historical_portfolios',[]):
            lines.append(f"Historical appointment: {h.get('portfolio','')} ({h.get('term','date not verified')})")
        aliases=ALIASES.get(normalized(name),[])
        lines.append('Alternative search names: '+', '.join(aliases))
        entries.append({'id':'structured:person:'+hashlib.sha256(name.encode()).hexdigest()[:20],
                        'text':'\n'.join(lines),'filename':'mp_ministers_data.json','page':1,
                        'url':person.get('profile_source_url',''),'label':'Curated minister profile (JSON)',
                        'entity':name,'aliases':' | '.join(aliases),'kind':'minister_profile'})
    # Store entire versioned remuneration JSON in multiple bounded sections.
    for key,value in framework.items():
        text=f"2026 Singapore political remuneration framework. Section {key}: "+json.dumps(value,ensure_ascii=False,sort_keys=True)
        for n in range(0,len(text),1100):
            entries.append({'id':f'structured:pay:{key}:{n//1100}', 'text':text[n:n+1100],
                            'filename':'remuneration_framework_2026.json','page':1,
                            'url':'','label':'Curated remuneration framework (JSON)',
                            'entity':'remuneration','aliases':'','kind':'remuneration_framework'})
    return entries

def sync_structured(collection,base:Path):
    entries=structured_entries(base)
    desired={e['id'] for e in entries}
    existing=set(collection.get(where={'source_kind':'structured'},include=[])['ids'])
    stale=sorted(existing-desired)
    if stale:collection.delete(ids=stale)
    # Avoid re-embedding unchanged records; content hashes ensure updated JSON is re-indexed.
    present=collection.get(ids=sorted(existing & desired),include=['metadatas']) if existing & desired else {'ids':[],'metadatas':[]}
    prior={i:m.get('content_hash') for i,m in zip(present['ids'],present['metadatas'])}
    changed=[]
    for e in entries:
        digest=hashlib.sha256(e['text'].encode('utf-8')).hexdigest()
        if prior.get(e['id'])!=digest:changed.append((e,digest))
    for i in range(0,len(changed),40):
        batch=changed[i:i+40]
        collection.upsert(ids=[e['id'] for e,_ in batch],documents=[e['text'] for e,_ in batch],
            metadatas=[{'doc_id':e['id'],'filename':e['filename'],'page':1,'source_url':e['url'],
                        'source_label':e['label'],'source_kind':'structured','entity':e['entity'],
                        'aliases':e['aliases'],'kind':e['kind'],'content_hash':h} for e,h in batch])
    return {'expected':len(entries),'updated':len(changed),'removed':len(stale),'indexed':len(desired)}

def lexical_matches(collection,question,limit=4):
    """Exact entity/alias lookup before semantic similarity. No guess on ambiguous names."""
    q=normalized(question)
    if not q:return []
    data=collection.get(where={'source_kind':'structured'},include=['documents','metadatas'])
    hits=[]
    for id_,text,meta in zip(data['ids'],data['documents'],data['metadatas']):
        if meta.get('kind')!='minister_profile':continue
        name=normalized(meta.get('entity',''))
        aliases=[normalized(a) for a in meta.get('aliases','').split('|') if a.strip()]
        tokens=[name]+aliases
        score=0
        for token in tokens:
            if token and re.search(r'(?<![a-z0-9])'+re.escape(token)+r'(?![a-z0-9])',q):
                score=max(score,100+len(token))
        if score:
            hits.append((score,{'text':text,'filename':meta['filename'],'page':1,'url':meta.get('source_url',''),
                 'label':meta.get('source_label',''),'distance':0.0,'match_type':'exact_name','entity':meta.get('entity','')}))
    hits.sort(key=lambda x:-x[0])
    return [e for _,e in hits[:limit]]
