"""Regression smoke tests for the offline Wikidata quality audit."""
import importlib.util
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "analysis" / "audit_wikidata_quality.py"
spec = importlib.util.spec_from_file_location("audit_wikidata_quality", MODULE)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class WikidataAuditTests(unittest.TestCase):
    def setUp(self):
        self.candidate = {
            "source_row": "0", "surface": "while", "qid": "Q1",
            "status": "unique_human_name_candidate", "mentions": "100",
            "documents": "10", "title_doc_count": "0", "person_label": "While"
        }
        self.screened = {
            "source_row": "0", "surface": "while", "qid": "Q1",
            "screen_status": "retained", "country": "France",
            "country_basis": "citizenship_fallback", "office_qids": ""
        }

    def test_high_risk_single_token(self):
        result, queue = audit.audit([self.candidate], [self.screened])
        self.assertEqual(result["retained_forms"], 1)
        self.assertEqual(result["high_risk_unreviewed_single_token"]["forms"], 1)
        self.assertEqual(queue[0]["issue"], "single_token_retained")

    def test_misaligned_rows_fail_closed(self):
        with self.assertRaises(ValueError):
            audit.audit([self.candidate], [{**self.screened, "surface": "whilst"}])

    def test_academic_public_office_is_flagged_for_review(self):
        row = {**self.screened, "screen_status": "excluded_academic", "office_qids": "Q123"}
        result, queue = audit.audit([self.candidate], [row])
        self.assertEqual(result["excluded_academic_with_offices"], 1)
        self.assertEqual(queue[0]["issue"], "academic_exclusion_with_office")


if __name__ == "__main__":
    unittest.main()
