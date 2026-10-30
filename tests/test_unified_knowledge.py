import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from rag.knowledge import structured_entries,lexical_matches,sync_structured

BASE=Path(__file__).resolve().parents[1]
class FakeCollection:
    def __init__(self):self.rows={}
    def get(self,where=None,include=None,ids=None):
        found=[(k,v) for k,v in self.rows.items() if (ids is None or k in ids) and (not where or all(v[1].get(a)==b for a,b in where.items()))]
        return {'ids':[k for k,v in found],'documents':[v[0] for k,v in found],'metadatas':[v[1] for k,v in found]}
    def upsert(self,ids,documents,metadatas):
        for i,d,m in zip(ids,documents,metadatas):self.rows[i]=(d,m)
    def delete(self,ids):
        for i in ids:self.rows.pop(i,None)

class KnowledgeTests(unittest.TestCase):
    def test_profiles_and_pay_are_indexed(self):
        entries=structured_entries(BASE)
        self.assertEqual(sum(e['kind']=='minister_profile' for e in entries),21)
        self.assertTrue(any(e['entity']=='Jasmin Lau' for e in entries))
        self.assertTrue(any(e['entity']=='Lee Hsien Loong' for e in entries))
        self.assertTrue(any(e['kind']=='remuneration_framework' for e in entries))
    def test_sync_idempotent_and_names(self):
        c=FakeCollection()
        a=sync_structured(c,BASE);self.assertEqual(a['updated'],a['expected'])
        self.assertEqual(sync_structured(c,BASE)['updated'],0)
        self.assertEqual(lexical_matches(c,'Who is jasmin?')[0]['entity'],'Jasmin Lau')
        self.assertEqual(lexical_matches(c,'Tell me about Senior Minister Lee')[0]['entity'],'Lee Hsien Loong')
        self.assertEqual(lexical_matches(c,'Who is Jasmine Lau?')[0]['entity'],'Jasmin Lau')
    def test_removal_and_update(self):
        c=FakeCollection();sync_structured(c,BASE)
        c.rows['structured:old']=('stale',{'source_kind':'structured'})
        self.assertEqual(sync_structured(c,BASE)['removed'],1)
        self.assertNotIn('structured:old',c.rows)
    def test_uploaded_docs_not_deleted(self):
        c=FakeCollection();c.rows['uploaded:1']=('Document text',{'source_kind':'uploaded'})
        sync_structured(c,BASE);self.assertIn('uploaded:1',c.rows)

if __name__=='__main__':unittest.main()
