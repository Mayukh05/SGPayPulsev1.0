import unittest, sys, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from profile_search import load_profiles,profile_answer
from remuneration import load_framework,salary_answer

class TestCabinet2026(unittest.TestCase):
 def test_all_21(self):
  p=load_profiles();self.assertEqual(len(p),21)
  self.assertIn('Lawrence Wong',p);self.assertIn('Jasmin Lau',p)
 def test_sources(self):
  for person in load_profiles().values():
   self.assertTrue(person['profile_source_url'].startswith('https://www.pmo.gov.sg/'))
   self.assertTrue(person['current_appointment'])
   self.assertIsNone(person['individual_actual_salary_sgd'])
   for h in person['historical_portfolios']:
    self.assertTrue(h['source_url'].startswith('https://www.pmo.gov.sg/'))
 def test_current_changes(self):
  p=load_profiles();self.assertIn('Defence',p['Chan Chun Sing']['current_appointment']);self.assertIn('Education',p['Desmond Lee']['current_appointment']);self.assertIn('Energy',p['Tan See Leng']['current_appointment'])
 def test_named_salary_no_invention(self):
  for name in load_profiles():
   if name=='Lawrence Wong':continue
   ans=salary_answer('What is '+name+' salary?')
   self.assertIn('not established',ans.lower(),name)
 def test_pay_rates(self):
  d={r['id']:r for r in load_framework()['rates']}
  self.assertEqual(d['pm']['current'],3600000)
  self.assertEqual(d['mr4']['current'],1800000)
  self.assertEqual(d['mp']['current'],18500)
 def test_history(self):
  a=profile_answer('What was Chan Chun Sing previous appointment?')
  self.assertIn('Education',a);self.assertIn('source',a)
 def test_minister_list(self):
  self.assertIn('Jasmin Lau',profile_answer('List all cabinet ministers'))
 def test_unknown(self):
  self.assertIsNone(profile_answer('random unrelated nonsense'))
if __name__=='__main__':unittest.main()
