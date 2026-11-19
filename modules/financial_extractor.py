import re
import math
from typing import List, Dict, Any, Optional, Tuple
from config import CANONICAL_TAXONOMY, SUPPORTED_SCALES

class FinancialExtractor:
    def __init__(self):
        self.taxonomy = CANONICAL_TAXONOMY

    def parse_number(self, text: str) -> Tuple[Optional[float], bool]:
        """
        Parses numeric strings from financial reports.
        Supports:
        - Indian commas: 1,25,000.00
        - Standard commas: 125,000.00
        - Parentheses for negative: (1,250.50) -> -1250.50
        - Trailing minus: 1250- -> -1250
        - Percentages: 15.5% -> 15.5
        Returns: (parsed_float, is_negative)
        """
        if not text:
            return None, False

        clean = text.strip()
        # Check negative parentheses: e.g. (1,250.00) or ( 1,250 )
        is_negative = False
        paren_match = re.match(r"^\s*\(\s*([0-9,\.\s]+)\s*\)\s*$", clean)
        if paren_match:
            is_negative = True
            clean = paren_match.group(1).strip()
        elif clean.startswith("-") or clean.endswith("-"):
            is_negative = True
            clean = clean.replace("-", "").strip()

        # Remove currency symbols and footnote markers
        clean = re.sub(r"[₹$€£¥%*†#]", "", clean).strip()

        # Remove commas
        clean_no_commas = clean.replace(",", "").replace(" ", "")

        try:
            val = float(clean_no_commas)
            if is_negative:
                val = -val
            return val, is_negative
        except ValueError:
            return None, False

    def match_canonical_metric(self, row_label: str, statement_hint: Optional[str] = None) -> Tuple[Optional[str], Optional[str], float]:
        """
        Fuzzy/exact matching of line item label to canonical metric code.
        Distinguishes compound labels like 'Total Liabilities and Equity' from 'Total Liabilities'.
        Returns: (metric_code, statement_type, confidence)
        """
        normalized_label = re.sub(r"[^a-zA-Z0-9\s]", "", row_label).strip().lower()
        if not normalized_label or len(normalized_label) < 3:
            return None, None, 0.0

        # Special compound exclusion
        if "liabilities" in normalized_label and "equity" in normalized_label:
            return "total_liabilities_and_equity", "balance_sheet", 0.95

        best_metric = None
        best_stmt = None
        highest_score = 0.0

        for stmt, metrics in self.taxonomy.items():
            for metric, keywords in metrics.items():
                for kw in keywords:
                    clean_kw = re.sub(r"[^a-zA-Z0-9\s]", "", kw).lower()
                    if normalized_label == clean_kw:
                        return metric, stmt, 1.0
                    elif clean_kw in normalized_label or normalized_label in clean_kw:
                        # Exact word boundary overlap
                        words_label = set(normalized_label.split())
                        words_kw = set(clean_kw.split())
                        overlap = len(words_label.intersection(words_kw))
                        score = overlap / max(len(words_label), len(words_kw))
                        if score > highest_score:
                            highest_score = score
                            best_metric = metric
                            best_stmt = stmt

        if highest_score >= 0.60:
            return best_metric, best_stmt, round(highest_score, 2)
        return None, None, 0.0

    def extract_from_tables(
        self,
        tables: List[Dict[str, Any]],
        default_currency: str = "INR",
        default_scale: str = "crores",
        default_period: str = "FY 2024-25"
    ) -> Dict[str, Any]:
        """
        Extracts structured financial facts from detected tables with full source locators.
        """
        extracted_facts: List[Dict[str, Any]] = []
        seen_metrics = set()

        for table in tables:
            page_no = table.get("page_no", 1)
            table_id = table.get("table_id", "tbl_1")
            headers = table.get("headers", [])
            rows = table.get("rows", [])
            stmt_type = table.get("statement_type", "Financial Statement")

            # Determine column periods from headers
            period_cols = self._detect_period_columns(headers, default_period)

            for r_idx, row in enumerate(rows):
                if not row:
                    continue
                row_label = str(row[0]).strip()
                if not row_label or row_label.lower() in ["particulars", "line item", "description", "assets", "liabilities"]:
                    continue

                metric_code, inferred_stmt, conf = self.match_canonical_metric(row_label, stmt_type)

                # Iterate through value columns
                for col_idx, (col_name, col_period) in period_cols.items():
                    if col_idx >= len(row):
                        continue
                    raw_cell = str(row[col_idx]).strip()
                    num_val, is_neg = self.parse_number(raw_cell)

                    if num_val is not None:
                        fact_id = f"fact_{table_id}_r{r_idx}_c{col_idx}"
                        scale_mult = SUPPORTED_SCALES.get(default_scale.lower(), 1.0)
                        base_val = num_val * scale_mult

                        fact_record = {
                            "fact_id": fact_id,
                            "metric_code": metric_code or f"custom_{re.sub(r'[^a-z0-9_]', '', row_label.lower().replace(' ', '_'))[:30]}",
                            "raw_label": row_label,
                            "canonical_metric": metric_code,
                            "raw_value_text": raw_cell,
                            "normalized_value": num_val,
                            "base_unit_value": base_val,
                            "currency": default_currency.upper(),
                            "scale": default_scale.lower(),
                            "period": col_period,
                            "statement_type": inferred_stmt or stmt_type,
                            "source_locator": {
                                "page_no": page_no,
                                "table_id": table_id,
                                "row_index": r_idx + 1,
                                "col_index": col_idx + 1,
                                "row_label": row_label,
                                "column_header": col_name
                            },
                            "extraction_confidence": conf if metric_code else 0.5,
                            "review_status": "auto_extracted",
                            "audit_history": []
                        }
                        extracted_facts.append(fact_record)

        # Run reconciliation checks
        reconciliations = self._run_reconciliation(extracted_facts)

        return {
            "total_facts_extracted": len(extracted_facts),
            "extracted_facts": extracted_facts,
            "reconciliation": reconciliations
        }

    def _detect_period_columns(self, headers: List[str], default_period: str) -> Dict[int, Tuple[str, str]]:
        """
        Maps column index to (header_name, detected_period).
        """
        period_cols = {}
        for idx, h in enumerate(headers):
            if idx == 0:
                continue
            text = str(h).strip()
            # Search for FY 2024, FY 24, 2024, 2025, etc.
            match = re.search(r"(FY\s*\d{2,4}(?:-\d{2,4})?|\b20\d{2}\b)", text, re.IGNORECASE)
            detected_period = match.group(0).upper() if match else default_period
            period_cols[idx] = (text, detected_period)

        if not period_cols and len(headers) > 1:
            for idx in range(1, len(headers)):
                period_cols[idx] = (headers[idx], default_period)

        return period_cols

    def _run_reconciliation(self, facts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Checks accounting equations:
        1. Balance Sheet: Total Assets == Total Liabilities + Total Equity
        2. Income Statement: Gross Profit == Revenue - COGS
        """
        by_period_metric = {}
        for f in facts:
            period = f.get("period")
            metric = f.get("canonical_metric")
            val = f.get("normalized_value")
            if period and metric and val is not None:
                if period not in by_period_metric:
                    by_period_metric[period] = {}
                # Prioritize higher confidence
                if metric not in by_period_metric[period] or f.get("extraction_confidence", 0) > by_period_metric[period].get(f"{metric}_conf", 0):
                    by_period_metric[period][metric] = val
                    by_period_metric[period][f"{metric}_conf"] = f.get("extraction_confidence", 0)

        reconciliation_results = []
        for period, metrics in by_period_metric.items():
            # Check 1: Balance Sheet equation
            assets = metrics.get("total_assets")
            liabilities = metrics.get("total_liabilities")
            equity = metrics.get("total_equity")

            if assets is not None and liabilities is not None and equity is not None:
                calc_sum = liabilities + equity
                diff = abs(assets - calc_sum)
                pass_check = diff < 0.05 * abs(assets) if assets else False
                reconciliation_results.append({
                    "check_name": "Balance Sheet Balance Check (Assets = Liabilities + Equity)",
                    "period": period,
                    "lhs_metric": "total_assets",
                    "lhs_value": assets,
                    "rhs_metric": "total_liabilities + total_equity",
                    "rhs_value": calc_sum,
                    "difference": round(diff, 2),
                    "passed": pass_check,
                    "status": "Balanced" if pass_check else "Discrepancy Flagged",
                    "notes": "Verified within rounding tolerance." if pass_check else "Discrepancy detected between Total Assets and Total Liabilities + Equity."
                })

            # Check 2: Gross Profit equation
            rev = metrics.get("revenue")
            cogs = metrics.get("cost_of_goods_sold")
            gp = metrics.get("gross_profit")
            if rev is not None and cogs is not None and gp is not None:
                calc_gp = rev - cogs
                diff = abs(gp - calc_gp)
                pass_check = diff < 0.05 * abs(rev)
                reconciliation_results.append({
                    "check_name": "Gross Profit Check (Gross Profit = Revenue - COGS)",
                    "period": period,
                    "lhs_metric": "gross_profit",
                    "lhs_value": gp,
                    "rhs_metric": "revenue - cogs",
                    "rhs_value": calc_gp,
                    "difference": round(diff, 2),
                    "passed": pass_check,
                    "status": "Balanced" if pass_check else "Discrepancy Flagged",
                    "notes": "Gross profit ties back to revenue minus COGS." if pass_check else "Gross profit differs from reported Revenue minus COGS."
                })

        return {
            "checks_run": len(reconciliation_results),
            "results": reconciliation_results,
            "all_passed": all(r.get("passed", False) for r in reconciliation_results) if reconciliation_results else True
        }

    def extract_from_text(
        self,
        pages_data: List[Dict[str, Any]],
        default_currency: str = "INR",
        default_scale: str = "crores",
        default_period: str = "FY 2024-25"
    ) -> Dict[str, Any]:
        """
        Fallback extractor that scans raw document text using canonical regex patterns
        when tables are unavailable or empty.
        """
        extracted_facts: List[Dict[str, Any]] = []
        scale_mult = SUPPORTED_SCALES.get(default_scale.lower(), 1.0)
        found_metrics = set()

        for page in pages_data:
            page_no = page.get("page_no", 1)
            text = page.get("text", "")
            lines = [l.strip() for l in text.split("\n") if l.strip()]

            for r_idx, line in enumerate(lines):
                for stmt, metrics in self.taxonomy.items():
                    for metric, keywords in metrics.items():
                        if metric in found_metrics:
                            continue
                        for kw in keywords:
                            pat = rf"\b{re.escape(kw)}\b[:\s\-—]+(?:[\$₹€£]?)\s*([\(\-0-9,\.\)]+)"
                            m = re.search(pat, line, re.IGNORECASE)
                            if m:
                                raw_val = m.group(1).strip()
                                num_val, is_neg = self.parse_number(raw_val)
                                if num_val is not None:
                                    found_metrics.add(metric)
                                    fact_id = f"fact_txt_p{page_no}_{len(extracted_facts)+1}"
                                    base_val = num_val * scale_mult
                                    extracted_facts.append({
                                        "fact_id": fact_id,
                                        "metric_code": metric,
                                        "raw_label": kw.title(),
                                        "canonical_metric": metric,
                                        "raw_value_text": raw_val,
                                        "normalized_value": num_val,
                                        "base_unit_value": base_val,
                                        "currency": default_currency.upper(),
                                        "scale": default_scale.lower(),
                                        "period": default_period,
                                        "statement_type": stmt,
                                        "source_locator": {
                                            "page_no": page_no,
                                            "table_id": "narrative_text",
                                            "row_index": r_idx + 1,
                                            "col_index": 1,
                                            "row_label": line[:60],
                                            "column_header": default_period
                                        },
                                        "extraction_confidence": 0.75,
                                        "review_status": "auto_extracted",
                                        "audit_history": []
                                    })
                                    break

        reconciliations = self._run_reconciliation(extracted_facts)
        return {
            "total_facts_extracted": len(extracted_facts),
            "extracted_facts": extracted_facts,
            "reconciliation": reconciliations
        }

financial_extractor = FinancialExtractor()
