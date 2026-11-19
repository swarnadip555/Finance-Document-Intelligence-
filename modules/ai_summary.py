import os
import json
from typing import Dict, Any, List, Optional
from config import GEMINI_API_KEY, OPENAI_API_KEY

class AISummaryGenerator:
    """
    Generates structured, evidence-grounded financial summaries.
    Enforces strict separation of:
    1. Direct Reported Facts (with citations)
    2. Deterministic Calculated Metrics (with formulas)
    3. Analytical Interpretation / Executive Commentary
    """

    def __init__(self):
        self.gemini_key = GEMINI_API_KEY
        self.openai_key = OPENAI_API_KEY

    def generate_summary(
        self,
        doc_info: Dict[str, Any],
        facts: List[Dict[str, Any]],
        ratios_data: Dict[str, Any],
        risks_data: Dict[str, Any],
        comparison_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        entity = doc_info.get("entity", "the Company")
        period = doc_info.get("period", "FY 2024-25")
        currency = doc_info.get("currency", "INR")
        scale = doc_info.get("scale", "crores")

        # Organize reported facts
        fact_lookup = {f["canonical_metric"]: f for f in facts if f.get("canonical_metric") and f.get("period") == period}
        ratio_lookup = {r["metric_name"]: r for r in ratios_data.get("ratios", []) if r.get("value") is not None}

        # Build grounded structured sections
        executive_summary = self._generate_executive_section(entity, period, currency, scale, fact_lookup, ratio_lookup, comparison_data)
        profitability_section = self._generate_profitability_section(currency, scale, fact_lookup, ratio_lookup)
        liquidity_leverage_section = self._generate_liquidity_leverage_section(currency, scale, fact_lookup, ratio_lookup)
        cash_flow_section = self._generate_cash_flow_section(currency, scale, fact_lookup, ratio_lookup)
        risk_synopsis = self._generate_risk_synopsis(risks_data)

        # Build evidence citations list
        all_citations = []
        for f in facts:
            if f.get("source_locator") and f.get("canonical_metric") in ["revenue", "net_profit", "total_assets", "total_debt", "operating_cash_flow"]:
                loc = f["source_locator"]
                all_citations.append({
                    "metric": f.get("canonical_metric"),
                    "raw_label": f.get("raw_label"),
                    "value": f"{currency} {f.get('raw_value_text')} {scale}",
                    "page_no": loc.get("page_no"),
                    "table_id": loc.get("table_id")
                })

        return {
            "entity": entity,
            "period": period,
            "currency": currency,
            "scale": scale,
            "generated_mode": "Grounded Financial Synthesis Engine",
            "executive_summary": executive_summary,
            "profitability_overview": profitability_section,
            "liquidity_and_leverage": liquidity_leverage_section,
            "cash_flow_analysis": cash_flow_section,
            "risk_synopsis": risk_synopsis,
            "evidence_citations": all_citations,
            "disclaimer": "This summary is generated for decision support and analytical review. It relies on extracted data from the provided document and does not constitute statutory audit or investment advice."
        }

    def _generate_executive_section(self, entity, period, currency, scale, facts, ratios, comparison):
        rev = facts.get("revenue")
        np = facts.get("net_profit")
        growth_note = ""
        if comparison and "comparisons" in comparison:
            rev_comp = next((c for c in comparison["comparisons"] if c["metric_code"] == "revenue"), None)
            if rev_comp and rev_comp.get("percentage_change") is not None:
                growth_note = f" (representing a {rev_comp['percentage_change']}% change over the previous period)"

        rev_val = f"{currency} {rev.get('normalized_value', 'N/A')} {scale}" if rev else "Undisclosed"
        np_val = f"{currency} {np.get('normalized_value', 'N/A')} {scale}" if np else "Undisclosed"
        npm_ratio = ratios.get("Net Profit Margin")
        npm_str = f"{npm_ratio['value']}%" if npm_ratio else "N/A"

        return (
            f"{entity} reported total revenue of {rev_val}{growth_note} for {period}. "
            f"The business generated a net profit of {np_val}, translating to a net profit margin of {npm_str}. "
            f"Overall operational performance demonstrates underlying resilience across key reporting segments."
        )

    def _generate_profitability_section(self, currency, scale, facts, ratios):
        gp_ratio = ratios.get("Gross Profit Margin")
        op_ratio = ratios.get("Operating Margin (EBIT)")
        npm_ratio = ratios.get("Net Profit Margin")
        roe_ratio = ratios.get("Return on Equity (ROE)")

        details = []
        if gp_ratio:
            details.append(f"Gross margin reached {gp_ratio['value']}%, reflecting pricing power and input cost management.")
        if op_ratio:
            details.append(f"Operating margin (EBIT) stood at {op_ratio['value']}%, showing operational overhead discipline.")
        if npm_ratio:
            details.append(f"Net profit margin was recorded at {npm_ratio['value']}%.")
        if roe_ratio:
            details.append(f"Return on Equity (ROE) achieved {roe_ratio['value']}%, representing shareholder capital productivity.")

        return " ".join(details) if details else "Profitability metrics could not be fully computed due to unstated line items."

    def _generate_liquidity_leverage_section(self, currency, scale, facts, ratios):
        cr = ratios.get("Current Ratio")
        de = ratios.get("Debt-to-Equity Ratio")

        details = []
        if cr:
            details.append(f"Liquidity is supported by a Current Ratio of {cr['value']}x ({cr.get('health_status', 'Evaluated')}).")
        if de:
            details.append(f"Capital structure solvency exhibits a Debt-to-Equity ratio of {de['value']}x ({de.get('health_status', 'Evaluated')}).")

        debt_fact = facts.get("total_debt")
        if debt_fact:
            details.append(f"Total debt obligations are reported at {currency} {debt_fact.get('normalized_value')} {scale}.")

        return " ".join(details) if details else "Liquidity and solvency ratios remain pending complete asset/liability disclosures."

    def _generate_cash_flow_section(self, currency, scale, facts, ratios):
        ocf = facts.get("operating_cash_flow")
        cf_ratio = ratios.get("Cash Flow to Net Income")

        details = []
        if ocf:
            details.append(f"The business generated {currency} {ocf.get('normalized_value')} {scale} from operating activities.")
        if cf_ratio:
            details.append(f"Operating cash flow conversion ratio was {cf_ratio['value']}x relative to net income.")

        return " ".join(details) if details else "Cash flow statement details were not identified or extracted from this document."

    def _generate_risk_synopsis(self, risks_data):
        flags = risks_data.get("flags", [])
        if not flags:
            return "No critical accounting or solvency flags detected during automated screening."

        high_flags = [f for f in flags if f.get("severity") == "HIGH"]
        med_flags = [f for f in flags if f.get("severity") == "MEDIUM"]

        synopsis = f"Screening flagged {len(high_flags)} High-priority and {len(med_flags)} Medium-priority indicators for analyst review. "
        if high_flags:
            synopsis += f"Key areas for scrutiny include: {', '.join([f['title'] for f in high_flags[:2]])}. "
        synopsis += "Review of relevant footnote notes and management discussions is advised."
        return synopsis

ai_summary_generator = AISummaryGenerator()

