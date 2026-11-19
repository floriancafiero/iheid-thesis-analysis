import importlib.util
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().with_name('rebuild_iheid_trends.py')
spec = importlib.util.spec_from_file_location('rebuild_iheid_trends', MODULE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class RebuildTests(unittest.TestCase):
    def test_no_automatic_generic_persons(self):
        self.assertEqual(m.check_multitoken('part ii', 'Part II')[0], False)
        self.assertEqual(m.check_multitoken("l'empereur", "L'Empereur")[0], False)
        self.assertEqual(m.check_multitoken('de gaulle', 'Charles de Gaulle')[0], False)
        self.assertTrue(m.check_multitoken('sumner welles', 'Sumner Welles')[0])

    def test_conservative_cross_source_dedup(self):
        items = [
            ('IHEID_abc','Two independent essays',2020,100000,'IHEID'),
            ('100123','Two independent essays',2020,100050,'IHEID'),
            ('IHEID_generic','Three essays in economics',2022,30000,'IHEID'),
            ('100124','Three essays in economics',2022,90000,'IHEID'),
            ('HEI_volume1','French policy historical',1966,140000,'HEI'),
            ('HEI_volume2','French policy historical',1966,320000,'HEI')
        ]
        meta={i: {'doc_id':i,'title':t,'year':str(y),'words_processed':str(n),'institution':inst}
              for i,t,y,n,inst in items}
        rows, dropped=m.audit_title_duplicates(meta)
        self.assertEqual(dropped, {'IHEID_abc'})
        self.assertEqual(len(rows),3)

    def test_manual_curated_figure_rescued(self):
        curated = ({'de gaulle':{'qid':'Q2042','name':'Charles de Gaulle','country':'France',
                               'basis':'curated_office','channel':'curated_exact'}},
                   {'Q2042':('Charles de Gaulle','France')}, {'Q2042':{'de gaulle'}})
        c=[{'source_row':'0','surface':'de gaulle','qid':'Q2042',
            'person_label':'Charles de Gaulle','mentions':'1184'}]
        s=[{'source_row':'0','surface':'de gaulle','qid':'Q2042','status':'unique_human_name_candidate',
            'screen_status':'unmapped_jurisdiction'}]
        ids,audit,_,_=m.identify(c,s,curated)
        self.assertEqual(ids['de gaulle']['country'],'France')
        self.assertEqual(audit[0]['action'],'curated_exact')

    def test_row_mismatch_fail_closed(self):
        curated=({}, {}, {})
        c=[{'source_row':'0','surface':'de gaulle','qid':'Q2042','person_label':'Charles de Gaulle'}]
        s=[{'source_row':'0','surface':'de gaull','qid':'Q2042','status':'unique_human_name_candidate',
            'screen_status':'unmapped_jurisdiction'}]
        with self.assertRaises(ValueError):m.identify(c,s,curated)

if __name__=='__main__': unittest.main()
