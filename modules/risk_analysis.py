from typing import List, Dict, Any, Optional

class RiskAnalyzer:
    """
    Automated Financial Risk & Anomaly Highlighting Engine.
    Evaluates liquidity stress, leverage spikes, margin degradation,
    cash flow divergence, and accounting reconciliation discrepancies.
    Every flag includes evidence citations, severity, and analytical caveats.
    """

    def analyze_risks(
        self,
        facts: List[Dict[str, Any]],
        calculated_ratios: List[Dict[str, Any]],
        reconciliation_data: Optional[Dict[str, Any]] = None,
        comparison_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        flags: List[Dict[str, Any]] = []

        # Map ratios by metric name
        ratio_map = {r["metric_name"]: r for r in calculated_ratios if r.get("value") is not None}

        # 1. Liquidity Stress Check
        current_ratio = ratio_map.get("Current Ratio")
        if current_ratio:
            cr_val = current_ratio["value"]
            if cr_val < 1.0:
                flags.append({
                    "id": "RISK_LIQ_01",
                    "title": "Severe Liquidity Strain (Current Ratio < 1.0x)",
                    "category": "Liquidity",
                    "severity": "HIGH",
                    "indicator_value": f"{cr_val}x",
                    "description": f"Current assets ({cr_val}x) are insufficient to cover short-term liabilities due within one year.",
                    "evidence": current_ratio.get("citations", []),
                    "caveat": "Screening indicator only. Company may have unused credit lines, short operating cash cycles, or high inventory turnover.",
                    "analyst_action": "Inspect upcoming debt maturities, debt covenants, and trade credit terms."
                })
            elif cr_val < 1.3:
                flags.append({
                    "id": "RISK_LIQ_02",
                    "title": "Tight Working Capital Buffer (Current Ratio < 1.3x)",
                    "category": "Liquidity",
                    "severity": "MEDIUM",
                    "indicator_value": f"{cr_val}x",
                    "description": f"Current ratio of {cr_val}x provides a slender buffer against receivables delay or inventory obsolescence.",
                    "evidence": current_ratio.get("citations", []),
                    "caveat": "Evaluate industry norms; asset-light service and software companies often operate comfortably near 1.2x.",
                    "analyst_action": "Review aging schedule of trade receivables."
                })

        # 2. High Leverage Check
        de_ratio = ratio_map.get("Debt-to-Equity Ratio")
        if de_ratio:
            de_val = de_ratio["value"]
            if de_val > 2.5:
                flags.append({
                    "id": "RISK_LEV_01",
                    "title": "Elevated Solvency Leverage (Debt/Equity > 2.5x)",
                    "category": "Leverage",
                    "severity": "HIGH",
                    "indicator_value": f"{de_val}x",
                    "description": f"Debt stands at {de_val}x total equity, indicating significant financial gearing and potential sensitivity to interest rate hikes.",
                    "evidence": de_ratio.get("citations", []),
                    "caveat": "Capital-intensive infrastructure, telecom, or utility sectors frequently operate with debt ratios above 2.0x.",
                    "analyst_action": "Review interest coverage ratio, debt amortization schedule, and credit ratings."
                })
            elif de_val > 1.8:
                flags.append({
                    "id": "RISK_LEV_02",
                    "title": "Moderate Financial Gearing (Debt/Equity > 1.8x)",
                    "category": "Leverage",
                    "severity": "MEDIUM",
                    "indicator_value": f"{de_val}x",
                    "description": f"Debt-to-equity ratio of {de_val}x reflects substantial borrowing relative to net worth.",
                    "evidence": de_ratio.get("citations", []),
                    "caveat": "High gearing can enhance return on equity during expansionary periods.",
                    "analyst_action": "Assess fixed charge coverage and refinancing risks."
                })

        # 3. Quality of Earnings / Cash Flow Divergence
        cf_ratio = ratio_map.get("Cash Flow to Net Income")
        if cf_ratio:
            cf_val = cf_ratio["value"]
            if cf_val < 0.5:
                flags.append({
                    "id": "RISK_QOE_01",
                    "title": "Weak Cash Conversion / Earnings Quality Alert",
                    "category": "Cash Generation",
                    "severity": "HIGH",
                    "indicator_value": f"{cf_val}x",
                    "description": f"Operating cash flow represents only {cf_val}x of reported accounting net income, indicating potential aggressive revenue recognition or ballooning uncollected receivables.",
                    "evidence": cf_ratio.get("citations", []),
                    "caveat": "Rapid expansion can naturally tie up capital in working capital buildup.",
                    "analyst_action": "Reconcile operating cash flow bridge and investigate non-cash profit adjustments."
                })
            elif cf_val < 0.8:
                flags.append({
                    "id": "RISK_QOE_02",
                    "title": "Moderate Cash Conversion Lag",
                    "category": "Cash Generation",
                    "severity": "MEDIUM",
                    "indicator_value": f"{cf_val}x",
                    "description": f"Operating cash flow to net income is {cf_val}x, below the 1.0x parity benchmark.",
                    "evidence": cf_ratio.get("citations", []),
                    "caveat": "Check for seasonal working capital fluctuations near fiscal year-end.",
                    "analyst_action": "Check inventory days and debtor turnover trends."
                })

        # 4. Period-over-period comparisons (if available)
        if comparison_data and "comparisons" in comparison_data:
            comp_list = comparison_data["comparisons"]
            rev_comp = next((c for c in comp_list if c["metric_code"] == "revenue"), None)
            if rev_comp and rev_comp.get("percentage_change") is not None:
                rev_growth = rev_comp["percentage_change"]
                if rev_growth < -5.0:
                    flags.append({
                        "id": "RISK_REV_01",
                        "title": f"Top-Line Contraction ({rev_growth}%)",
                        "category": "Growth & Performance",
                        "severity": "HIGH" if rev_growth < -15.0 else "MEDIUM",
                        "indicator_value": f"{rev_growth}% YoY",
                        "description": f"Reported revenue dropped {abs(rev_growth)}% compared to the prior period.",
                        "evidence": [rev_comp.get("citations", {}).get("current")],
                        "caveat": "Disinvestment of business segments, currency translation, or customer consolidation may explain the dip.",
                        "analyst_action": "Analyze volume vs price variations and segment-wise disclosures."
                    })

            # Check Margin Compression
            gp_comp = next((c for c in comp_list if c["metric_code"] == "gross_profit"), None)
            if rev_comp and gp_comp and rev_comp.get("percentage_change") is not None and gp_comp.get("percentage_change") is not None:
                if gp_comp["percentage_change"] < rev_comp["percentage_change"] - 5.0:
                    flags.append({
                        "id": "RISK_MAR_01",
                        "title": "Gross Margin Squeeze Detected",
                        "category": "Profitability",
                        "severity": "MEDIUM",
                        "indicator_value": f"GP Growth: {gp_comp['percentage_change']}% vs Rev: {rev_comp['percentage_change']}%",
                        "description": "Cost of goods sold grew faster than revenue, squeezing gross margins.",
                        "evidence": [gp_comp.get("citations", {}).get("current")],
                        "caveat": "Raw material inflation or promotional pricing during new market entry could cause temporary pressure.",
                        "analyst_action": "Review raw materials cost disclosures and commodity hedging policies."
                    })

        # 5. Reconciliation Discrepancies
        if reconciliation_data and "results" in reconciliation_data:
            for check in reconciliation_data["results"]:
                if not check.get("passed", True):
                    flags.append({
                        "id": "RISK_REC_01",
                        "title": f"Accounting Equation Discrepancy: {check.get('check_name')}",
                        "category": "Reporting Fidelity",
                        "severity": "HIGH",
                        "indicator_value": f"Diff: {check.get('difference')}",
                        "description": f"Reported {check.get('lhs_metric')} ({check.get('lhs_value')}) does not match {check.get('rhs_metric')} ({check.get('rhs_value')}).",
                        "evidence": [],
                        "caveat": "Could stem from rounding differences, unextracted minority interest, or differing line item definitions.",
                        "analyst_action": "Inspect original statement footnotes for restatements or reclassifications."
                    })

        # If no severe flags found, add positive/neutral health indicators
        if not flags:
            flags.append({
                "id": "HEALTH_01",
                "title": "Stable Financial Screening Profile",
                "category": "General",
                "severity": "LOW",
                "indicator_value": "Optimal",
                "description": "Standard screening criteria for liquidity, leverage, and statement balancing met without severe anomalies.",
                "evidence": [],
                "caveat": "Automated screening covers standard financial metrics only; thorough qualitative analysis is recommended.",
                "analyst_action": "Proceed with regular valuation and governance assessment."
            })

        # Summary counts
        high_cnt = sum(1 for f in flags if f.get("severity") == "HIGH")
        med_cnt = sum(1 for f in flags if f.get("severity") == "MEDIUM")
        low_cnt = sum(1 for f in flags if f.get("severity") in ["LOW", "NEUTRAL"])

        return {
            "total_risk_flags": len(flags),
            "severity_counts": {
                "high": high_cnt,
                "medium": med_cnt,
                "low": low_cnt
            },
            "overall_risk_profile": "Elevated Caution" if high_cnt >= 2 else ("Moderate Risk" if (high_cnt == 1 or med_cnt >= 2) else "Low / Stable Risk"),
            "disclaimer": "All risk indicators are algorithmic screening signals intended for analyst review, not definitive declarations of fraud, default, or audit qualifications.",
            "flags": flags
        }

risk_analyzer = RiskAnalyzer()

