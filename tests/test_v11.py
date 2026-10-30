import json
import sys
from pathlib import Path
import pytest
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
from rag.engine import extract_text,split_text,evidence_answer,seed_documents,DocumentStore

def test_roster():
    d=json.loads((BASE/'data/mp_ministers_data.json').read_text())
    assert len(d)==21
    assert 'Lawrence Wong' in d
    assert all('current_appointment' in p and 'constituency' in p for p in d.values())

def test_salary_source_and_types():
    d=json.loads((BASE/'data/remuneration_framework_2026.json').read_text())
    r={r['id']:r for r in d['rates']}
    assert r['pm']['current']==3600000
    assert r['mr4']['current']==1800000
    assert r['mp']['current']==18500
    assert r['mr4']['kind']=='framework_reference'
    assert d['sources']

def test_chunk_overlap():
    text=' '.join('word'+str(i) for i in range(600))
    chunks=split_text(text,200,30)
    assert len(chunks)>2
    assert all(len(c)<=200 for c in chunks)
    assert chunks[0].split()[-1] in chunks[1]

def test_text_extraction():
    assert extract_text(b'hello world','.txt')[0]['text']=='hello world'
    with pytest.raises(ValueError):extract_text(b'hello','.exe')

def test_docx_sample():
    p=BASE/'sample_documents'/'project_proposal.docx'
    text=' '.join(x['text'] for x in extract_text(p.read_bytes(),'.docx'))
    assert 'SGPayPulse' in text

def test_pdf_sample():
    p=BASE/'sample_documents'/'2017_salary_review.pdf'
    pages=extract_text(p.read_bytes(),'.pdf')
    assert len(pages)>=15
    assert 'SALAR' in ' '.join(x['text'] for x in pages).upper()

def test_evidence_answer_no_key():
    ans,kind=evidence_answer('MR4',[{'filename':'source.pdf','page':3,'text':'MR4 reference framework','url':'https://example.com','label':'source'}])
    assert kind=='extractive' and 'source.pdf' in ans

def test_evidence_answer_no_results():
    ans,kind=evidence_answer('unknown',[])
    assert kind=='no_evidence'

def test_project_pages_present():
    app=(BASE/'SGPayPulsev1.0.py').read_text()
    for text in ['Minister Comparator','2026 Pay Explorer','Document Manager','Methodology','About Us','AI Assistant']:
        assert text in app
    assert 'hmac.compare_digest' in app

def test_sources_are_not_personal_pay():
    d=json.loads((BASE/'data/mp_ministers_data.json').read_text())
    assert all(p.get('individual_actual_salary_sgd') is None for p in d.values())
