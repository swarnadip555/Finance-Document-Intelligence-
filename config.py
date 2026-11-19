import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
PROCESSED_DIR = DATA_DIR / "processed"
VECTOR_DB_DIR = BASE_DIR / "vector_db"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

MAX_FILE_SIZE_MB = 50
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}

SUPPORTED_CURRENCIES = ["USD", "INR", "EUR", "GBP", "JPY", "CAD", "AUD"]
SUPPORTED_SCALES = {
    "units": 1.0,
    "thousands": 1_000.0,
    "lakhs": 100_000.0,
    "millions": 1_000_000.0,
    "crores": 10_000_000.0,
    "billions": 1_000_000_000.0,
}

CANONICAL_TAXONOMY = {
    "balance_sheet": {
        "total_assets": ["total assets", "total asset", "assets total"],
        "current_assets": ["total current assets", "current assets"],
        "cash_and_equivalents": ["cash and cash equivalents", "cash and bank balances", "cash & cash equivalents", "cash"],
        "accounts_receivable": ["trade receivables", "accounts receivable", "receivables"],
        "inventory": ["inventories", "inventory", "stock in trade"],
        "total_liabilities": ["total liabilities", "liabilities total"],
        "current_liabilities": ["total current liabilities", "current liabilities"],
        "total_debt": ["total debt", "total borrowings", "borrowings"],
        "short_term_debt": ["short-term borrowings", "short term debt", "current borrowings"],
        "long_term_debt": ["long-term borrowings", "long term debt", "non-current borrowings"],
        "total_equity": ["total equity", "shareholders' equity", "stockholders' equity", "total shareholders equity", "net worth"],
        "retained_earnings": ["retained earnings", "reserves and surplus", "other equity"],
    },
    "income_statement": {
        "revenue": ["revenue from operations", "revenue", "total revenue", "sales", "turnover", "net sales"],
        "cost_of_goods_sold": ["cost of revenue", "cost of goods sold", "cogs", "cost of materials consumed"],
        "gross_profit": ["gross profit", "gross margin"],
        "operating_expenses": ["total operating expenses", "operating expenses", "other expenses"],
        "ebitda": ["ebitda", "operating profit before depreciation"],
        "ebit": ["operating profit", "ebit", "profit before finance costs and tax", "operating income"],
        "finance_costs": ["finance costs", "interest expense", "finance charges", "interest costs"],
        "tax_expense": ["tax expense", "income tax", "provision for tax"],
        "net_profit": ["profit for the year", "profit for the period", "net profit", "net income", "profit after tax"],
    },
    "cash_flow": {
        "operating_cash_flow": ["cash generated from operations", "net cash from operating activities", "operating cash flow"],
        "investing_cash_flow": ["net cash used in investing activities", "investing cash flow", "cash flows from investing activities"],
        "financing_cash_flow": ["net cash used in financing activities", "financing cash flow", "cash flows from financing activities"],
        "capital_expenditures": ["purchase of property, plant and equipment", "capital expenditure", "capex"],
        "free_cash_flow": ["free cash flow"],
        "net_change_in_cash": ["net increase in cash and cash equivalents", "net change in cash"],
    }
}

RISK_THRESHOLDS = {
    "current_ratio_critical": 1.0,
    "current_ratio_warning": 1.3,
    "debt_to_equity_high": 2.0,
    "debt_to_equity_moderate": 1.5,
    "margin_compression_pct": 2.0,
    "revenue_decline_pct": 0.0,
    "ocf_to_net_income_ratio": 0.7,
}

