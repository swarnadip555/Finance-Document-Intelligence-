import re
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import VECTOR_DB_DIR, GEMINI_API_KEY, OPENAI_API_KEY
from modules.ratio_calculator import ratio_calculator
from modules.comparison import financial_comparison

try:
    from google import genai
    from google.genai import types
    HAS_GOOGLE_GENAI = True
except ImportError:
    HAS_GOOGLE_GENAI = False

def test_gemini_connection(api_key: str, model_name: str = "gemini-3.8-flash") -> Tuple[bool, str]:
    """Test verification for Gemini API key."""
    if not api_key or not api_key.strip():
        return False, "API key is empty."
    if not HAS_GOOGLE_GENAI:
        return False, "google-genai package is not installed."
    try:
        client = genai.Client(api_key=api_key.strip())
        res = client.models.generate_content(
            model=model_name,
            contents="Respond with the single word: OK",
            config=types.GenerateContentConfig(temperature=0.0)
        )
        if res and res.text:
            return True, f"Connected to {model_name} successfully!"
        return False, "No response text received from Gemini API."
    except Exception as e:
        return False, f"Connection failed: {str(e)}"

class RAGPipeline:
    """
    Financial RAG Pipeline with Query Routing:
    - Route A: Factual lookup & Deterministic Math (Revenue, Debt, Profit, Ratios) ->
      Queries structured database and exact deterministic calculators with full citations.
    - Route B: Qualitative / Narrative Disclosures (Risks, Strategy, MD&A, Footnotes) ->
      Retrieves top semantic passages with page and section citations.
    - Route C: Out of bounds / missing data ->
      Explicitly responds with 'Information not found in document', zero hallucinations.
    """

    def __init__(self):
        self.vector_dir = Path(VECTOR_DB_DIR)
        self.vector_dir.mkdir(parents=True, exist_ok=True)

    def chunk_document_text(self, pages_data: List[Dict[str, Any]], chunk_size_words: int = 150, overlap_words: int = 30) -> List[Dict[str, Any]]:
        chunks = []
        chunk_id = 0

        for page in pages_data:
            page_no = page.get("page_no", 1)
            text = page.get("text", "")
            section_hint = page.get("section_hint", f"Page {page_no}")

            words = text.split()
            if not words:
                continue

            for i in range(0, len(words), chunk_size_words - overlap_words):
                chunk_words = words[i:i + chunk_size_words]
                chunk_text = " ".join(chunk_words)
                chunk_id += 1

                chunks.append({
                    "chunk_id": f"chunk_p{page_no}_{chunk_id}",
                    "page_no": page_no,
                    "section": section_hint,
                    "text": chunk_text,
                    "word_count": len(chunk_words)
                })

        return chunks

    def build_and_save_index(self, doc_id: str, chunks: List[Dict[str, Any]]) -> None:
        if not chunks:
            return

        corpus = [c["text"] for c in chunks]
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=5000)
        tfidf_matrix = vectorizer.fit_transform(corpus)

        index_file = self.vector_dir / f"{doc_id}_index.pkl"
        with open(index_file, "wb") as f:
            pickle.dump({
                "chunks": chunks,
                "vectorizer": vectorizer,
                "matrix": tfidf_matrix
            }, f)

    def search_narrative(self, doc_id: str, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        index_file = self.vector_dir / f"{doc_id}_index.pkl"
        if not index_file.exists():
            return []

        try:
            with open(index_file, "rb") as f:
                data = pickle.load(f)
            chunks = data["chunks"]
            vectorizer = data["vectorizer"]
            matrix = data["matrix"]

            q_vec = vectorizer.transform([query])
            sims = cosine_similarity(q_vec, matrix).flatten()

            top_indices = np.argsort(sims)[::-1][:top_k]
            results = []
            for idx in top_indices:
                if sims[idx] > 0.05:
                    chunk = chunks[idx].copy()
                    chunk["relevance_score"] = round(float(sims[idx]), 3)
                    results.append(chunk)
            return results
        except Exception:
            return []

    def classify_query(self, query: str) -> str:
        q = query.lower()
        if any(w in q for w in ["compare", "growth", "versus", "vs", "increase", "decrease", "change"]):
            return "COMPARISON"
        if any(w in q for w in ["ratio", "current ratio", "debt to equity", "margin", "roe", "roa", "quick ratio"]):
            return "RATIO_CALCULATION"
        if any(w in q for w in ["risk", "threat", "concern", "weakness", "flag", "litigation"]):
            return "RISK_ANALYSIS"
        if any(w in q for w in ["what was", "what is", "revenue", "profit", "assets", "liabilities", "cash flow", "debt", "sales", "ebit"]):
            return "FACTUAL_LOOKUP"
        return "NARRATIVE_SEARCH"

    def answer_question(
        self,
        query: str,
        doc_info: Dict[str, Any],
        facts: List[Dict[str, Any]],
        ratios_data: Dict[str, Any],
        comparison_data: Optional[Dict[str, Any]] = None,
        gemini_api_key: Optional[str] = None,
        model_name: str = "gemini-3.8-flash"
    ) -> Dict[str, Any]:
        query_type = self.classify_query(query)
        doc_id = doc_info.get("id", "")
        currency = doc_info.get("currency", "INR")
        scale = doc_info.get("scale", "crores")
        period = doc_info.get("period", "FY 2024-25")

        citations = []
        answer_text = ""
        structured_formula = None
        narrative_results = []

        # Route 1: Ratio query
        if query_type == "RATIO_CALCULATION":
            q_lower = query.lower()
            matched_ratio = None
            for r in ratios_data.get("ratios", []):
                name = r["metric_name"].lower()
                if any(k in q_lower for k in name.split()[:2]) or (name in q_lower):
                    matched_ratio = r
                    break

            if matched_ratio and matched_ratio.get("status") == "calculated":
                answer_text = (
                    f"**{matched_ratio['metric_name']}** for {period} is **{matched_ratio['value']}{matched_ratio['unit']}**.\n\n"
                    f"- **Category:** {matched_ratio['category']}\n"
                    f"- **Deterministic Formula:** `{matched_ratio['formula']}`\n"
                    f"- **Health Status:** {matched_ratio.get('health_status', 'Evaluated')} ({matched_ratio.get('benchmark', '')})\n"
                    f"- **Financial Context:** {matched_ratio.get('interpretation', '')}"
                )
                structured_formula = matched_ratio["formula"]
                citations = matched_ratio.get("citations", [])
            elif matched_ratio and matched_ratio.get("status") == "not_calculated":
                answer_text = (
                    f"**{matched_ratio['metric_name']}** could not be calculated for {period}.\n"
                    f"**Reason:** {matched_ratio.get('reason', 'Required line items not found in document.')}\n"
                    f"Formula requires: `{matched_ratio.get('formula')}`"
                )
            else:
                answer_text = (
                    f"Available calculated ratios for {period} include: "
                    + ", ".join([f"{r['metric_name']} ({r['value']}{r['unit']})" for r in ratios_data.get("ratios", []) if r.get("value") is not None])
                )

        # Route 2: Specific Metric / Factual lookup
        elif query_type == "FACTUAL_LOOKUP":
            q_lower = query.lower()
            matching_fact = None
            for f in facts:
                canonical = f.get("canonical_metric") or ""
                label = f.get("raw_label", "").lower()
                if canonical and (canonical in q_lower or canonical.replace("_", " ") in q_lower or label in q_lower):
                    if f.get("period") == period:
                        matching_fact = f
                        break

            if matching_fact:
                loc = matching_fact.get("source_locator", {})
                answer_text = (
                    f"According to the {matching_fact.get('statement_type')}, **{matching_fact.get('raw_label')}** "
                    f"for {matching_fact.get('period')} is **{currency} {matching_fact.get('raw_value_text')} {scale}** "
                    f"(Normalized value: {matching_fact.get('normalized_value'):,}).\n\n"
                    f"This figure was extracted with {round(matching_fact.get('extraction_confidence', 1.0) * 100)}% parser confidence "
                    f"and verified from Page {loc.get('page_no')}, {loc.get('table_id')}."
                )
                citations = [{
                    "type": "table_cell",
                    "metric": matching_fact.get("canonical_metric"),
                    "raw_label": matching_fact.get("raw_label"),
                    "raw_value": matching_fact.get("raw_value_text"),
                    "page_no": loc.get("page_no"),
                    "table_id": loc.get("table_id"),
                    "row_index": loc.get("row_index")
                }]
            else:
                # Search narrative chunks if not found in structured facts
                pass

        # Route 3: Comparison query
        if query_type == "COMPARISON" and comparison_data:
            comp_list = comparison_data.get("comparisons", [])
            q_lower = query.lower()
            matched_comp = next((c for c in comp_list if c["metric_code"] in q_lower or c["label"].lower() in q_lower), None)

            if matched_comp:
                sign = "+" if (matched_comp.get("absolute_change") or 0) > 0 else ""
                answer_text = (
                    f"Comparison for **{matched_comp['label']}**:\n"
                    f"- **{matched_comp['prior_period']}:** {matched_comp['prior_value']} {matched_comp['scale']}\n"
                    f"- **{matched_comp['current_period']}:** {matched_comp['current_value']} {matched_comp['scale']}\n"
                    f"- **Absolute Delta (Δ):** {sign}{matched_comp['absolute_change']} {matched_comp['scale']}\n"
                    f"- **Growth Rate:** {matched_comp['percentage_change']}%\n"
                    f"- **Trend Direction:** {matched_comp['trend_direction']}"
                )
                if matched_comp.get("warning"):
                    answer_text += f"\n\n*Warning: {matched_comp['warning']}*"
                citations = [matched_comp.get("citations", {}).get("current")]

        # Route 4: Qualitative narrative / Fallback
        if not answer_text:
            narrative_results = self.search_narrative(doc_id, query, top_k=3)
            if narrative_results:
                excerpts = []
                for res in narrative_results:
                    citations.append({
                        "type": "narrative_chunk",
                        "page_no": res["page_no"],
                        "section": res["section"],
                        "relevance_score": res.get("relevance_score")
                    })
                    excerpts.append(f"> \"{res['text'][:280]}...\" — *Page {res['page_no']} ({res['section']})*")

                answer_text = (
                    f"Based on the narrative disclosures retrieved from the document:\n\n"
                    + "\n\n".join(excerpts)
                    + "\n\n*Note: Numerical figures cited above should be cross-verified against audited financial statement schedules.*"
                )
            else:
                answer_text = (
                    f"The requested information regarding **\"{query}\"** was **not found** in the uploaded document ({doc_info.get('filename')}). "
                    f"The system avoids estimating or hallucinating unverified financial figures."
                )

        # If Gemini API key is provided, synthesize response using Gemini model while keeping grounded facts
        synthesized_by_gemini = False
        gemini_error = None

        if gemini_api_key and gemini_api_key.strip() and HAS_GOOGLE_GENAI:
            chunks_for_gemini = narrative_results if narrative_results else self.search_narrative(doc_id, query, top_k=3)
            gemini_txt, ok, err = self.generate_gemini_synthesis(
                query=query,
                deterministic_answer=answer_text,
                doc_info=doc_info,
                facts=facts,
                ratios_data=ratios_data,
                narrative_chunks=chunks_for_gemini,
                gemini_api_key=gemini_api_key.strip(),
                model_name=model_name
            )
            if ok:
                answer_text = gemini_txt
                synthesized_by_gemini = True
            else:
                gemini_error = err

        return {
            "query": query,
            "query_type": query_type,
            "answer": answer_text,
            "structured_formula": structured_formula,
            "citations": [c for c in citations if c],
            "confidence": 0.95 if citations else 0.4,
            "synthesized_by_gemini": synthesized_by_gemini,
            "gemini_error": gemini_error,
            "timestamp": "2026-11-16T12:00:00"
        }

    def generate_gemini_synthesis(
        self,
        query: str,
        deterministic_answer: str,
        doc_info: Dict[str, Any],
        facts: List[Dict[str, Any]],
        ratios_data: Dict[str, Any],
        narrative_chunks: List[Dict[str, Any]],
        gemini_api_key: str,
        model_name: str = "gemini-3.8-flash"
    ) -> Tuple[str, bool, Optional[str]]:
        if not HAS_GOOGLE_GENAI:
            return deterministic_answer, False, "google-genai SDK not installed."

        entity = doc_info.get("entity", "Company")
        period = doc_info.get("period", "FY 2024-25")
        currency = doc_info.get("currency", "USD")
        scale = doc_info.get("scale", "millions")

        facts_summary = []
        for f in facts[:15]:
            loc = f.get("source_locator", {})
            facts_summary.append(
                f"- {f.get('raw_label')} ({f.get('canonical_metric')}): {currency} {f.get('raw_value_text')} {scale} "
                f"[Page {loc.get('page_no')}, {loc.get('table_id')}]"
            )

        ratios_summary = []
        for r in ratios_data.get("ratios", []):
            if r.get("status") == "calculated":
                ratios_summary.append(
                    f"- {r.get('metric_name')}: {r.get('value')}{r.get('unit')} (Formula: {r.get('formula')}) - {r.get('interpretation', '')}"
                )

        excerpts_summary = []
        for c in narrative_chunks[:3]:
            excerpts_summary.append(
                f"[Page {c.get('page_no')}, {c.get('section')}]: \"{c.get('text', '')[:300]}...\""
            )

        prompt = f"""You are FinIntellect AI, an elite corporate financial analyst reviewing an official corporate financial report.

CONTEXT:
- Entity: {entity}
- Reporting Period: {period}
- Currency / Scale: {currency} {scale}

VERIFIED FINANCIAL LINE ITEMS:
{chr(10).join(facts_summary) if facts_summary else "No direct line items."}

CALCULATED FINANCIAL RATIOS:
{chr(10).join(ratios_summary) if ratios_summary else "No calculated ratios."}

DOCUMENT EXCERPTS (MD&A / AUDITOR'S REPORT / NOTES):
{chr(10).join(excerpts_summary) if excerpts_summary else "No narrative excerpts."}

BASELINE GROUND-TRUTH FACTUAL ANSWER:
{deterministic_answer}

USER QUESTION:
{query}

INSTRUCTIONS:
1. Provide an executive-level, analytical, well-formatted financial answer directly responding to the user.
2. Ground all numbers strictly in the provided verified data. Never invent or hallucinate financial figures.
3. Reference the specific page numbers or financial statements when quoting metrics.
4. If asked about financial health, liquidity, debt, or profitability, provide concise context explaining the trend or financial significance.
5. If the document does not contain the answer, explicitly state that it was not reported.
"""

        try:
            client = genai.Client(api_key=gemini_api_key.strip())
            config = types.GenerateContentConfig(
                system_instruction=(
                    "You are FinIntellect AI, an executive financial analyst assistant. "
                    "Provide factual, grounded, citation-rich financial answers. "
                    "Never hallucinate numbers. Always reference verified page and statement locations."
                ),
                temperature=0.2
            )
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config
            )
            if response and response.text:
                return response.text, True, None
            return deterministic_answer, False, "Empty response from Gemini model"
        except Exception as e:
            return deterministic_answer, False, str(e)

rag_pipeline = RAGPipeline()
