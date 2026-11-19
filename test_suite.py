import unittest
from modules.financial_extractor import financial_extractor
from modules.ratio_calculator import ratio_calculator
from modules.comparison import financial_comparison
from modules.risk_analysis import risk_analyzer
from modules.rag_pipeline import rag_pipeline

class TestFinancialIntelligencePipeline(unittest.TestCase):

    def test_number_parsing(self):
        # Test standard numbers
        val, is_neg = financial_extractor.parse_number("125,000.50")
        self.assertEqual(val, 125000.50)
        self.assertFalse(is_neg)

        # Test negative parentheses
        val_neg, is_neg2 = financial_extractor.parse_number("(1,250.75)")
        self.assertEqual(val_neg, -1250.75)
        self.assertTrue(is_neg2)

        # Test Indian numbering format
        val_ind, _ = financial_extractor.parse_number("14,500.00")
        self.assertEqual(val_ind, 14500.0)

        # Test percentages
        val_pct, _ = financial_extractor.parse_number("18.5%")
        self.assertEqual(val_pct, 18.5)

    def test_deterministic_ratios(self):
        sample_facts = [
            {"canonical_metric": "current_assets", "normalized_value": 8900.0, "period": "FY25", "currency": "INR", "scale": "crores", "source_locator": {"page_no": 3, "table_id": "tbl_2", "row_index": 1}},
            {"canonical_metric": "current_liabilities", "normalized_value": 4800.0, "period": "FY25", "currency": "INR", "scale": "crores", "source_locator": {"page_no": 3, "table_id": "tbl_2", "row_index": 7}},
            {"canonical_metric": "total_debt", "normalized_value": 3300.0, "period": "FY25", "currency": "INR", "scale": "crores", "source_locator": {"page_no": 3, "table_id": "tbl_2", "row_index": 11}},
            {"canonical_metric": "total_equity", "normalized_value": 12000.0, "period": "FY25", "currency": "INR", "scale": "crores", "source_locator": {"page_no": 3, "table_id": "tbl_2", "row_index": 13}},
            {"canonical_metric": "revenue", "normalized_value": 14500.0, "period": "FY25", "currency": "INR", "scale": "crores", "source_locator": {"page_no": 2, "table_id": "tbl_1", "row_index": 1}},
            {"canonical_metric": "net_profit", "normalized_value": 2420.0, "period": "FY25", "currency": "INR", "scale": "crores", "source_locator": {"page_no": 2, "table_id": "tbl_1", "row_index": 12}},
            {"canonical_metric": "operating_cash_flow", "normalized_value": 2850.0, "period": "FY25", "currency": "INR", "scale": "crores", "source_locator": {"page_no": 4, "table_id": "tbl_3", "row_index": 1}},
        ]

        res = ratio_calculator.calculate_ratios_for_period(sample_facts, "FY25")
        ratios_map = {r["metric_name"]: r for r in res["ratios"]}

        # Current ratio: 8900 / 4800 = 1.854 -> 1.85
        self.assertEqual(ratios_map["Current Ratio"]["value"], 1.85)
        self.assertEqual(ratios_map["Current Ratio"]["health_status"], "Healthy")

        # Debt to equity: 3300 / 12000 = 0.275 -> 0.28
        self.assertEqual(ratios_map["Debt-to-Equity Ratio"]["value"], 0.28)

        # Net Profit Margin: (2420 / 14500) * 100 = 16.689 -> 16.69
        self.assertEqual(ratios_map["Net Profit Margin"]["value"], 16.69)

        # Cash Flow to Net Income: 2850 / 2420 = 1.177 -> 1.18
        self.assertEqual(ratios_map["Cash Flow to Net Income"]["value"], 1.18)

    def test_missing_input_handling(self):
        incomplete_facts = [
            {"canonical_metric": "current_assets", "normalized_value": 1000.0, "period": "FY25"}
        ]
        res = ratio_calculator.calculate_ratios_for_period(incomplete_facts, "FY25")
        cr = next(r for r in res["ratios"] if r["metric_name"] == "Current Ratio")
        self.assertEqual(cr["status"], "not_calculated")
        self.assertIn("Missing Current Liabilities", cr["reason"])

    def test_period_comparison(self):
        facts = [
            {"canonical_metric": "revenue", "normalized_value": 14500.0, "period": "FY25", "currency": "INR", "scale": "crores"},
            {"canonical_metric": "revenue", "normalized_value": 12200.0, "period": "FY24", "currency": "INR", "scale": "crores"}
        ]
        comp = financial_comparison.compare_periods(facts, "FY25", "FY24")
        rev_comp = comp["comparisons"][0]
        self.assertEqual(rev_comp["absolute_change"], 2300.0)
        self.assertEqual(rev_comp["percentage_change"], 18.85)
        self.assertEqual(rev_comp["trend_direction"], "Growth")

    def test_query_classification(self):
        self.assertEqual(rag_pipeline.classify_query("What is the current ratio?"), "RATIO_CALCULATION")
        self.assertEqual(rag_pipeline.classify_query("What is the total revenue?"), "FACTUAL_LOOKUP")
        self.assertEqual(rag_pipeline.classify_query("Compare revenue growth vs prior year"), "COMPARISON")
        self.assertEqual(rag_pipeline.classify_query("What are the key risk factors in MD&A?"), "RISK_ANALYSIS")

if __name__ == "__main__":
    unittest.main()

