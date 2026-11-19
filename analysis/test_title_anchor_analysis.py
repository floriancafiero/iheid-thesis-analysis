import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('title_anchor_validation',ROOT/'title_anchor_validation.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
p=importlib.util.spec_from_file_location('title_person_checks',ROOT/'title_person_checks.py')
people=importlib.util.module_from_spec(p);p.loader.exec_module(people)

class TitleAnchorTests(unittest.TestCase):
 def test_strict_country_boundaries(self):
  self.assertIn('France',m.title_matches('Comparative law in France and Israel',m.COUNTRIES))
  self.assertIn('Israel',m.title_matches('Comparative law in France and Israel',m.COUNTRIES))
  self.assertNotIn('United States',m.title_matches('Between us: a history',m.COUNTRIES))
  self.assertNotIn('United States',m.title_matches('The Americas in perspective',m.COUNTRIES))
 def test_historical_states_are_separate(self):
  self.assertEqual(set(m.title_matches('The USSR and modern Russia',m.COUNTRIES)),{'Soviet Union','Russia'})
  self.assertIn('Zaire',m.title_matches('Commerce au Zaire',m.COUNTRIES))
  self.assertNotIn('DR Congo',m.title_matches('Commerce au Zaire',m.COUNTRIES))
 def test_organization_canonical_ids(self):
  self.assertEqual(m.ORG_NER_LABELS['UE'],'UE/EU')
  self.assertEqual(m.ORG_NER_LABELS['CE'],'CE/EC')
  self.assertEqual(m.ORG_NER_LABELS['CEE'],'CEE/EEC')
  self.assertNotIn('ONU',m.title_matches('UN cooperation',m.ORGANIZATIONS))
 def test_academic_can_be_title_topic(self):
  self.assertTrue(people.admissible('frédéric bastiat','Frédéric Bastiat'))
  self.assertTrue(people.admissible('franklin d roosevelt','Franklin Delano Roosevelt'))
  self.assertFalse(people.admissible('the italian','Carlo Costanzia'))
  self.assertFalse(people.admissible('président carter','Jimmy Carter'))
  self.assertFalse(people.admissible('roosevelt','Franklin Delano Roosevelt'))
 def test_interval(self):
  lo,hi=m.wilson(184,190)
  self.assertTrue(93<lo<97 and 97<hi<100)

if __name__=='__main__':unittest.main()
