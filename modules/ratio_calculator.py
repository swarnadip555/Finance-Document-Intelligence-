from typing import List, Dict, Any, Optional

class RatioCalculator:
    """
    Deterministic Financial Ratio Calculator.
    All calculations are performed strictly via mathematical formulas in code.
    LLMs are never used for arithmetic.
    """

    def calculate_ratios_for_period(self, facts: List[Dict[str, Any]], period: str) -> Dict[str, Any]:
        # Filter facts for target period
        metrics: Dict[str, Dict[str, Any]] = {}
        for f in facts:
            if f.get("period") == period and f.get("canonical_metric"):
                code = f["canonical_metric"]
                # Only keep highest confidence or first if duplicates
                if code not in metrics or f.get("extraction_confidence", 0) > metrics[code].get("extraction_confidence", 0):
                    metrics[code] = f

        def get_val(code: str) -> Optional[float]:
            fact = metrics.get(code)
            return fact.get("normalized_value") if fact else None

        def get_citation(code: str) -> Optional[Dict[str, Any]]:
            fact = metrics.get(code)
            if not fact:
                return None
            loc = fact.get("source_locator", {})
            return {
                "metric_code": code,
                "raw_label": fact.get("raw_label"),
                "raw_value": fact.get("raw_value_text"),
                "normalized_value": fact.get("normalized_value"),
                "page_no": loc.get("page_no"),
                "table_id": loc.get("table_id"),
                "row_index": loc.get("row_index")
            }

        calculated_ratios = []

        # 1. Current Ratio
        ca = get_val("current_assets")
        cl = get_val("current_liabilities")
        if ca is not None and cl is not None and cl != 0:
            val = round(ca / cl, 2)
            calculated_ratios.append({
                "metric_name": "Current Ratio",
                "category": "Liquidity",
                "formula": "Current Assets ÷ Current Liabilities",
                "value": val,
                "unit": "x",
                "status": "calculated",
                "benchmark": "≥ 1.33x desirable",
                "health_status": "Healthy" if val >= 1.3 else ("Moderate" if val >= 1.0 else "Critical"),
                "inputs": {
                    "current_assets": ca,
                    "current_liabilities": cl
                },
                "citations": [get_citation("current_assets"), get_citation("current_liabilities")],
                "interpretation": f"The company holds {val}x of current assets for every unit of short-term liability."
            })
        else:
            reason = "Missing Current Liabilities (or zero)" if cl in (None, 0) else "Missing Current Assets"
            calculated_ratios.append({
                "metric_name": "Current Ratio",
                "category": "Liquidity",
                "formula": "Current Assets ÷ Current Liabilities",
                "value": None,
                "unit": "x",
                "status": "not_calculated",
                "reason": reason,
                "inputs": {},
                "citations": []
            })

        # 2. Quick Ratio
        inv = get_val("inventory") or 0.0
        if ca is not None and cl is not None and cl != 0:
            val = round((ca - inv) / cl, 2)
            calculated_ratios.append({
                "metric_name": "Quick Ratio (Acid Test)",
                "category": "Liquidity",
                "formula": "(Current Assets − Inventory) ÷ Current Liabilities",
                "value": val,
                "unit": "x",
                "status": "calculated",
                "benchmark": "≥ 1.0x desirable",
                "health_status": "Healthy" if val >= 1.0 else "Moderate",
                "inputs": {
                    "current_assets": ca,
                    "inventory": inv,
                    "current_liabilities": cl
                },
                "citations": [get_citation("current_assets"), get_citation("current_liabilities")],
                "interpretation": f"Quick ratio stands at {val}x, testing immediate liquid obligations without relying on inventory sales."
            })

        # 3. Debt to Equity
        debt = get_val("total_debt")
        if debt is None:
            # Try sum of short and long term debt
            st = get_val("short_term_debt") or 0.0
            lt = get_val("long_term_debt") or 0.0
            if st + lt > 0:
                debt = st + lt

        eq = get_val("total_equity")
        if debt is not None and eq is not None and eq != 0:
            val = round(debt / eq, 2)
            calculated_ratios.append({
                "metric_name": "Debt-to-Equity Ratio",
                "category": "Solvency & Leverage",
                "formula": "Total Borrowings ÷ Total Equity",
                "value": val,
                "unit": "x",
                "status": "calculated",
                "benchmark": "≤ 1.5x conservative",
                "health_status": "Healthy" if val <= 1.5 else ("Moderate" if val <= 2.5 else "High Leverage"),
                "inputs": {"total_debt": debt, "total_equity": eq},
                "citations": [get_citation("total_debt") or get_citation("short_term_debt"), get_citation("total_equity")],
                "interpretation": f"The company employs {val}x debt financing relative to shareholders' equity capital."
            })
        else:
            reason = "Missing Total Debt or Total Equity" if eq is None or debt is None else "Zero Equity"
            calculated_ratios.append({
                "metric_name": "Debt-to-Equity Ratio",
                "category": "Solvency & Leverage",
                "formula": "Total Borrowings ÷ Total Equity",
                "value": None,
                "unit": "x",
                "status": "not_calculated",
                "reason": reason,
                "inputs": {},
                "citations": []
            })

        # 4. Gross Margin
        rev = get_val("revenue")
        gp = get_val("gross_profit")
        cogs = get_val("cost_of_goods_sold")
        if gp is None and rev is not None and cogs is not None:
            gp = rev - cogs

        if rev is not None and gp is not None and rev != 0:
            val = round((gp / rev) * 100, 2)
            calculated_ratios.append({
                "metric_name": "Gross Profit Margin",
                "category": "Profitability",
                "formula": "(Gross Profit ÷ Total Revenue) × 100",
                "value": val,
                "unit": "%",
                "status": "calculated",
                "benchmark": "Industry dependent",
                "health_status": "Healthy" if val >= 25.0 else "Moderate",
                "inputs": {"gross_profit": gp, "revenue": rev},
                "citations": [get_citation("gross_profit") or get_citation("revenue"), get_citation("revenue")],
                "interpretation": f"{val}% of total revenue is retained after direct production and delivery costs."
            })
        else:
            calculated_ratios.append({
                "metric_name": "Gross Profit Margin",
                "category": "Profitability",
                "formula": "(Gross Profit ÷ Total Revenue) × 100",
                "value": None,
                "unit": "%",
                "status": "not_calculated",
                "reason": "Missing Revenue or Gross Profit / COGS data",
                "inputs": {},
                "citations": []
            })

        # 5. Operating Margin (EBIT)
        ebit = get_val("ebit")
        if rev is not None and ebit is not None and rev != 0:
            val = round((ebit / rev) * 100, 2)
            calculated_ratios.append({
                "metric_name": "Operating Margin (EBIT)",
                "category": "Profitability",
                "formula": "(Operating Profit EBIT ÷ Total Revenue) × 100",
                "value": val,
                "unit": "%",
                "status": "calculated",
                "benchmark": "≥ 12.0% strong",
                "health_status": "Healthy" if val >= 12.0 else ("Moderate" if val >= 5.0 else "Weak"),
                "inputs": {"ebit": ebit, "revenue": rev},
                "citations": [get_citation("ebit"), get_citation("revenue")],
                "interpretation": f"Operating efficiency yields {val}% profit before interest and taxes from revenue."
            })

        # 6. Net Profit Margin
        np = get_val("net_profit")
        if rev is not None and np is not None and rev != 0:
            val = round((np / rev) * 100, 2)
            calculated_ratios.append({
                "metric_name": "Net Profit Margin",
                "category": "Profitability",
                "formula": "(Net Profit ÷ Total Revenue) × 100",
                "value": val,
                "unit": "%",
                "status": "calculated",
                "benchmark": "≥ 8.0% healthy",
                "health_status": "Healthy" if val >= 8.0 else ("Moderate" if val >= 2.0 else "Weak"),
                "inputs": {"net_profit": np, "revenue": rev},
                "citations": [get_citation("net_profit"), get_citation("revenue")],
                "interpretation": f"Bottom-line conversion of revenue to net profit is {val}%."
            })

        # 7. Return on Equity (ROE)
        if np is not None and eq is not None and eq != 0:
            val = round((np / eq) * 100, 2)
            calculated_ratios.append({
                "metric_name": "Return on Equity (ROE)",
                "category": "Profitability & Returns",
                "formula": "(Net Profit ÷ Shareholders' Equity) × 100",
                "value": val,
                "unit": "%",
                "status": "calculated",
                "benchmark": "≥ 15.0% superior",
                "health_status": "Healthy" if val >= 15.0 else ("Moderate" if val >= 8.0 else "Low"),
                "inputs": {"net_profit": np, "total_equity": eq},
                "citations": [get_citation("net_profit"), get_citation("total_equity")],
                "interpretation": f"Return generated on shareholders' capital is {val}%."
            })

        # 8. Return on Assets (ROA)
        ta = get_val("total_assets")
        if np is not None and ta is not None and ta != 0:
            val = round((np / ta) * 100, 2)
            calculated_ratios.append({
                "metric_name": "Return on Assets (ROA)",
                "category": "Profitability & Returns",
                "formula": "(Net Profit ÷ Total Assets) × 100",
                "value": val,
                "unit": "%",
                "status": "calculated",
                "benchmark": "≥ 5.0% solid",
                "health_status": "Healthy" if val >= 5.0 else "Moderate",
                "inputs": {"net_profit": np, "total_assets": ta},
                "citations": [get_citation("net_profit"), get_citation("total_assets")],
                "interpretation": f"The business yields {val}% return on its total asset base."
            })

        # 9. Cash Flow to Net Profit (Quality of Earnings)
        ocf = get_val("operating_cash_flow")
        if ocf is not None and np is not None and np != 0:
            val = round(ocf / np, 2)
            calculated_ratios.append({
                "metric_name": "Cash Flow to Net Income",
                "category": "Cash Flow & Earnings Quality",
                "formula": "Operating Cash Flow ÷ Net Profit",
                "value": val,
                "unit": "x",
                "status": "calculated",
                "benchmark": "≥ 1.0x strong cash conversion",
                "health_status": "Healthy" if val >= 1.0 else ("Moderate" if val >= 0.7 else "Earnings Quality Alert"),
                "inputs": {"operating_cash_flow": ocf, "net_profit": np},
                "citations": [get_citation("operating_cash_flow"), get_citation("net_profit")],
                "interpretation": f"Operating cash conversion represents {val}x of reported accounting net income."
            })

        return {
            "period": period,
            "ratios": calculated_ratios,
            "total_calculated": len([r for r in calculated_ratios if r.get("status") == "calculated"]),
            "total_uncalculated": len([r for r in calculated_ratios if r.get("status") == "not_calculated"])
        }

ratio_calculator = RatioCalculator()

