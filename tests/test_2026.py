import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from remuneration import load_framework,salary_answer
class Test2026(unittest.TestCase):
 def test_rates(self):
  d=load_framework(); self.assertEqual(d['rates'][0]['current'],3600000);self.assertEqual(d['rates'][2]['current'],18500)
 def test_pm(self):
  self.assertIn('S$3,600,000',salary_answer('Lawrence Wong salary'))
 def test_individual(self):
  self.assertIn('not established',salary_answer('Chan Chun Sing salary'))
 def test_mr4(self):
  self.assertIn('not automatically',salary_answer('MR4 salary increase'))
 def test_nonpay(self):
  self.assertIsNone(salary_answer('Who is Minister for Education?'))
if __name__=='__main__': unittest.main()
