import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ai.assistant import rag_answer,llm_answer,relevant_evidence
from ai.providers import configured_models,ModelOption,ModelError,classify_error

M=ModelOption('OpenAI','mini','gpt-4.1-mini')
E=[{'filename':'2017.pdf','page':4,'text':'Monthly salary and bonus components are documented.','distance':0.21,'url':'https://example.org'}]

def synth(model,settings,messages):
    assert 'Retrieved evidence:' in messages[-1]['content']
    return 'Fixed and variable pay [1].'

class AssistantTests(unittest.TestCase):
    def test_good_rag(self):
        x=rag_answer('How is salary calculated?',E,M,synth,{})
        self.assertEqual(x.status,'success');self.assertIn('[1]',x.text);self.assertEqual(len(x.evidence),1)
    def test_empty_rag(self):
        x=rag_answer('latest',[],M,synth,{})
        self.assertEqual(x.status,'insufficient_evidence');self.assertTrue(x.can_switch)
    def test_low_relevance(self):
        x=rag_answer('latest',[{**E[0],'distance':0.95}],M,synth,{})
        self.assertEqual(x.status,'insufficient_evidence')
    def test_model_refuses_unsupported(self):
        x=rag_answer('latest',E,M,lambda *args:'INSUFFICIENT_EVIDENCE',{})
        self.assertTrue(x.can_switch)
    def test_missing_model(self):
        x=rag_answer('question',E,None,synth,{})
        self.assertEqual(x.status,'configuration')
    def test_provider_error_keeps_evidence(self):
        def broken(*args):raise ModelError('connection','Cannot connect')
        x=rag_answer('question',E,M,broken,{})
        self.assertEqual(x.status,'api_error');self.assertEqual(x.error_category,'connection');self.assertEqual(len(x.evidence),1)
    def test_llm_mode_no_retrieval(self):
        x=llm_answer('hello',M,lambda m,s,msgs:'Hello',{})
        self.assertIn('not verified',x.text)
    def test_no_provider(self):
        self.assertEqual(configured_models({}),[])
    def test_openai_allowlist(self):
        models=configured_models({'OPENAI_API_KEY':'test','OPENAI_ALLOWED_MODELS':'gpt-4.1-mini,gpt-4.1'})
        self.assertEqual(len(models),2)
    def test_azure_deployments(self):
        models=configured_models({'AZURE_OPENAI_API_KEY':'test','AZURE_OPENAI_ENDPOINT':'https://example.openai.azure.com','AZURE_OPENAI_DEPLOYMENTS':'deployment-a,deployment-b'})
        self.assertEqual([x.model_id for x in models],['deployment-a','deployment-b'])
    def test_error_classification(self):
        self.assertEqual(classify_error(type('APIConnectionError',(Exception,),{})()).category,'connection')

if __name__=='__main__':unittest.main()
