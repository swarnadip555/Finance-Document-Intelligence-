import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import pdfplumber
import fitz
import docx

class TableExtractor:
    def __init__(self):
        pass

    def extract_tables(self, file_path: str) -> List[Dict[str, Any]]:
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext == ".pdf":
            return self._extract_pdf_tables(file_path)
        elif ext in [".docx", ".doc"]:
            return self._extract_docx_tables(file_path)
        return []

    def _classify_statement_type(self, title_text: str, header_text: str, rows_text: str) -> str:
        combined = f"{title_text} {header_text} {rows_text}".lower()
        if any(k in combined for k in ["balance sheet", "statement of financial position"]):
            return "Balance Sheet"
        if any(k in combined for k in ["statement of profit and loss", "income statement", "profit & loss", "statement of operations"]):
            return "Income Statement"
        if any(k in combined for k in ["cash flow statement", "statement of cash flows", "cash flows"]):
            return "Cash Flow Statement"
        if any(k in combined for k in ["ratio", "financial summary", "highlights"]):
            return "Financial Highlights"
        return "Financial Schedule / Table"

    def _extract_pdf_tables(self, file_path: str) -> List[Dict[str, Any]]:
        extracted_tables = []
        table_counter = 0

        # Primary extraction using pdfplumber for high table fidelity
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_idx, page in enumerate(pdf.pages):
                    page_no = page_idx + 1
                    raw_tables = page.extract_tables()

                    for t_idx, raw_table in enumerate(raw_tables):
                        if not raw_table or len(raw_table) < 2:
                            continue

                        # Clean cells
                        cleaned_rows = []
                        for row in raw_table:
                            cleaned_row = [str(cell).strip() if cell is not None else "" for cell in row]
                            # only keep if not all empty
                            if any(cleaned_row):
                                cleaned_rows.append(cleaned_row)

                        if len(cleaned_rows) < 2:
                            continue

                        table_counter += 1
                        headers = cleaned_rows[0]
                        data_rows = cleaned_rows[1:]

                        # Extract surrounding text to find title/caption
                        page_text = page.extract_text() or ""
                        first_row_str = " ".join(headers)
                        rows_sample_str = " ".join([" ".join(r) for r in data_rows[:3]])

                        statement_type = self._classify_statement_type(page_text[:200], first_row_str, rows_sample_str)

                        extracted_tables.append({
                            "table_id": f"tbl_p{page_no}_{t_idx+1}",
                            "table_index": table_counter,
                            "page_no": page_no,
                            "statement_type": statement_type,
                            "headers": headers,
                            "rows": data_rows,
                            "num_rows": len(data_rows),
                            "num_cols": len(headers),
                            "raw_text_summary": f"{statement_type} on Page {page_no} with {len(data_rows)} line items"
                        })
        except Exception:
            pass

        # Fallback 1: If pdfplumber found no tables, try PyMuPDF find_tables
        if not extracted_tables:
            try:
                doc = fitz.open(file_path)
                for page_idx, page in enumerate(doc):
                    page_no = page_idx + 1
                    tabs = page.find_tables()
                    for t_idx, tab in enumerate(tabs):
                        df = tab.extract()
                        if df and len(df) > 1:
                            table_counter += 1
                            headers = [str(c).strip() if c is not None else "" for c in df[0]]
                            data_rows = [[str(c).strip() if c is not None else "" for c in row] for row in df[1:]]
                            statement_type = self._classify_statement_type("", " ".join(headers), "")
                            extracted_tables.append({
                                "table_id": f"tbl_p{page_no}_{t_idx+1}",
                                "table_index": table_counter,
                                "page_no": page_no,
                                "statement_type": statement_type,
                                "headers": headers,
                                "rows": data_rows,
                                "num_rows": len(data_rows),
                                "num_cols": len(headers),
                                "raw_text_summary": f"{statement_type} on Page {page_no} with {len(data_rows)} rows"
                            })
            except Exception:
                pass

        # Fallback 2: Text-based financial table reconstruction for borderless or text-aligned tables
        if not extracted_tables:
            try:
                doc = fitz.open(file_path)
                for page_idx, page in enumerate(doc):
                    page_no = page_idx + 1
                    text = page.get_text("text")
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    parsed_rows = []
                    for line in lines:
                        # Match line with text label followed by 1 or more financial numbers
                        # e.g. "Revenue from operations  14,500.00  12,300.00"
                        m = re.findall(r"(\([0-9,\.]+\)|-?[0-9,]+\.[0-9]{2}|-?[0-9,]{3,})", line)
                        if m:
                            # Label is everything before the first number
                            first_num = m[0]
                            pos = line.find(first_num)
                            if pos > 2:
                                label = line[:pos].strip()
                                # Clean trailing dots, dashes, colons
                                label = re.sub(r"[\.:\-_]+$", "", label).strip()
                                if label and len(label) > 2 and not label.isnumeric():
                                    row_vals = [label] + [n.strip() for n in m]
                                    parsed_rows.append(row_vals)

                    if len(parsed_rows) >= 3:
                        table_counter += 1
                        # Estimate max columns
                        max_cols = max(len(r) for r in parsed_rows)
                        headers = ["Particulars"] + [f"Period {c}" for c in range(1, max_cols)]
                        # Normalize rows to max_cols
                        norm_rows = [r + [""] * (max_cols - len(r)) for r in parsed_rows]
                        statement_type = self._classify_statement_type(text[:200], " ".join(headers), "")
                        extracted_tables.append({
                            "table_id": f"tbl_text_p{page_no}_1",
                            "table_index": table_counter,
                            "page_no": page_no,
                            "statement_type": statement_type,
                            "headers": headers,
                            "rows": norm_rows,
                            "num_rows": len(norm_rows),
                            "num_cols": max_cols,
                            "raw_text_summary": f"Text-aligned {statement_type} on Page {page_no} with {len(norm_rows)} rows"
                        })
            except Exception:
                pass

        return extracted_tables

    def _extract_docx_tables(self, file_path: str) -> List[Dict[str, Any]]:
        extracted_tables = []
        try:
            doc = docx.Document(file_path)
            for t_idx, table in enumerate(doc.tables):
                rows_data = []
                for row in table.rows:
                    row_cells = [cell.text.strip() for cell in row.cells]
                    if any(row_cells):
                        rows_data.append(row_cells)

                if len(rows_data) < 2:
                    continue

                headers = rows_data[0]
                data_rows = rows_data[1:]
                statement_type = self._classify_statement_type("", " ".join(headers), " ".join([" ".join(r) for r in data_rows[:3]]))

                extracted_tables.append({
                    "table_id": f"tbl_docx_{t_idx+1}",
                    "table_index": t_idx + 1,
                    "page_no": 1,
                    "statement_type": statement_type,
                    "headers": headers,
                    "rows": data_rows,
                    "num_rows": len(data_rows),
                    "num_cols": len(headers),
                    "raw_text_summary": f"{statement_type} with {len(data_rows)} rows"
                })
        except Exception:
            pass

        return extracted_tables

table_extractor = TableExtractor()

