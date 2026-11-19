from typing import List, Dict, Any, Optional

class FinancialComparison:
    """
    Period-over-period and multi-document comparison engine.
    Calculates absolute delta and percentage growth rates.
    Ensures currency and scale compatibility.
    """

    def compare_periods(
        self,
        facts: List[Dict[str, Any]],
        current_period: str,
        prior_period: str
    ) -> Dict[str, Any]:
        curr_facts = {f["canonical_metric"]: f for f in facts if f.get("period") == current_period and f.get("canonical_metric")}
        prior_facts = {f["canonical_metric"]: f for f in facts if f.get("period") == prior_period and f.get("canonical_metric")}

        all_metrics = set(curr_facts.keys()).union(set(prior_facts.keys()))
        comparisons = []
        incompatible_warnings = []

        for metric in sorted(all_metrics):
            curr_item = curr_facts.get(metric)
            prior_item = prior_facts.get(metric)

            curr_val = curr_item.get("normalized_value") if curr_item else None
            prior_val = prior_item.get("normalized_value") if prior_item else None

            curr_curr = curr_item.get("currency") if curr_item else None
            prior_curr = prior_item.get("currency") if prior_item else None

            curr_scale = curr_item.get("scale") if curr_item else None
            prior_scale = prior_item.get("scale") if prior_item else None

            # Check compatibility
            is_compatible = True
            warning = None
            if curr_curr and prior_curr and curr_curr != prior_curr:
                is_compatible = False
                warning = f"Currency mismatch: {curr_curr} vs {prior_curr}"
                incompatible_warnings.append(f"{metric}: {warning}")

            if curr_scale and prior_scale and curr_scale != prior_scale:
                is_compatible = False
                warning = f"Scale mismatch: {curr_scale} vs {prior_scale}"
                incompatible_warnings.append(f"{metric}: {warning}")

            # Calculations
            abs_change = None
            pct_change = None
            trend_direction = "N/A"

            if is_compatible and curr_val is not None and prior_val is not None:
                abs_change = round(curr_val - prior_val, 2)
                if prior_val != 0:
                    pct_change = round(((curr_val - prior_val) / abs(prior_val)) * 100, 2)
                else:
                    pct_change = None

                if abs_change > 0:
                    trend_direction = "Growth"
                elif abs_change < 0:
                    trend_direction = "Decline"
                else:
                    trend_direction = "Unchanged"

            label = (curr_item or prior_item or {}).get("raw_label", metric.replace("_", " ").title())
            stmt = (curr_item or prior_item or {}).get("statement_type", "General")

            comparisons.append({
                "metric_code": metric,
                "label": label,
                "statement_type": stmt,
                "current_period": current_period,
                "current_value": curr_val,
                "prior_period": prior_period,
                "prior_value": prior_val,
                "currency": curr_curr or prior_curr,
                "scale": curr_scale or prior_scale,
                "absolute_change": abs_change,
                "percentage_change": pct_change,
                "trend_direction": trend_direction,
                "is_compatible": is_compatible,
                "warning": warning,
                "citations": {
                    "current": curr_item.get("source_locator") if curr_item else None,
                    "prior": prior_item.get("source_locator") if prior_item else None
                }
            })

        return {
            "current_period": current_period,
            "prior_period": prior_period,
            "total_metrics_compared": len(comparisons),
            "incompatible_warnings": list(set(incompatible_warnings)),
            "comparisons": comparisons
        }

financial_comparison = FinancialComparison()

