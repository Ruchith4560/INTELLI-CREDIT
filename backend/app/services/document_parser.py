import os
import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def parse_document(file_path: str, doc_type: str, ext: str) -> Dict[str, Any]:
    """
    Parse any uploaded document and return extracted text + structured data.
    Tries real libraries first; falls back to mock data for demo if unavailable.
    """
    result = {"text": "", "tables": [], "structured": {}}
    try:
        if ext == ".pdf":
            result = _parse_pdf(file_path, doc_type)
        elif ext == ".csv":
            result = _parse_csv(file_path)
        elif ext in [".xlsx", ".xls"]:
            result = _parse_excel(file_path)
        elif ext == ".txt":
            with open(file_path, "r", errors="ignore") as f:
                result["text"] = f.read()
        else:
            result["text"] = _generate_mock_text(doc_type)
    except Exception as e:
        logger.error(f"Document parse error: {e}")
        result["text"] = _generate_mock_text(doc_type)
        result["error"] = str(e)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# PDF PARSING  (STUB 1 — real libraries auto-used when installed)
# Install:  pip install PyMuPDF pdfplumber
# ─────────────────────────────────────────────────────────────────────────────

def _parse_pdf(file_path: str, doc_type: str) -> Dict[str, Any]:
    """
    PDF parsing pipeline:
      1. Try PyMuPDF  (fast, handles most PDFs)
      2. Try pdfplumber  (better for table-heavy PDFs)
      3. Try Tesseract OCR  (for scanned / image-based PDFs)
      4. Fall back to mock text  (demo mode)
    """
    text = ""
    tables = []

    # ── Step 1: PyMuPDF ──────────────────────────────────────────────────────
    try:
        import fitz  # PyMuPDF  — pip install PyMuPDF
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text()
        doc.close()
        if text.strip():
            logger.info("✅ PDF parsed with PyMuPDF")
    except ImportError:
        logger.warning("PyMuPDF not installed. Run: pip install PyMuPDF")
    except Exception as e:
        logger.warning(f"PyMuPDF failed: {e}")

    # ── Step 2: pdfplumber (better table extraction) ──────────────────────────
    if not text.strip():
        try:
            import pdfplumber  # pip install pdfplumber
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    text += page_text + "\n"
                    page_tables = page.extract_tables() or []
                    tables.extend(page_tables)
            if text.strip():
                logger.info("✅ PDF parsed with pdfplumber")
        except ImportError:
            logger.warning("pdfplumber not installed. Run: pip install pdfplumber")
        except Exception as e:
            logger.warning(f"pdfplumber failed: {e}")

    # ── Step 3: Tesseract OCR for scanned PDFs ────────────────────────────────
    # HOW TO ENABLE:
    #   1. Download Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
    #   2. Install:  pip install pytesseract Pillow PyMuPDF
    #   3. Set TESSERACT_PATH in your .env file, e.g.:
    #      TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
    if not text.strip():
        try:
            import pytesseract          # pip install pytesseract
            from PIL import Image       # pip install Pillow
            import fitz                 # pip install PyMuPDF

            tesseract_path = os.getenv("TESSERACT_PATH", "")
            if tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = tesseract_path

            doc = fitz.open(file_path)
            ocr_text = ""
            for page in doc:
                # Render page as high-res image for OCR
                pix = page.get_pixmap(dpi=300)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                ocr_text += pytesseract.image_to_string(img, lang="eng") + "\n"
            doc.close()

            if ocr_text.strip():
                text = ocr_text
                logger.info("✅ PDF parsed with Tesseract OCR (scanned PDF)")
        except ImportError:
            logger.warning("OCR libs not installed. Run: pip install pytesseract Pillow")
        except Exception as e:
            logger.warning(f"OCR failed: {e}")

    # ── Step 4: Mock fallback for demo ────────────────────────────────────────
    if not text.strip():
        logger.warning(f"⚠️  No text extracted from PDF. Using mock data for demo.")
        text = _generate_mock_text(doc_type)

    structured = _extract_structured(text, doc_type)
    return {"text": text, "tables": tables, "structured": structured}


# ─────────────────────────────────────────────────────────────────────────────
# CSV / EXCEL PARSING
# ─────────────────────────────────────────────────────────────────────────────

def _parse_csv(file_path: str) -> Dict[str, Any]:
    """Parse CSV files using pandas"""
    try:
        import pandas as pd
        df = pd.read_csv(file_path)
        # Remove unnamed columns
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
        text = df.to_string(index=False)
        summary = _summarise_dataframe(df)
        return {"text": text + "\n" + summary, "dataframe": df.head(50).to_dict(), "structured": {}}
    except Exception as e:
        logger.error(f"CSV parse error: {e}")
        return {"text": "", "error": str(e)}


def _parse_excel(file_path: str) -> Dict[str, Any]:
    """Parse Excel files using pandas"""
    try:
        import pandas as pd
        # Read all sheets
        xl = pd.ExcelFile(file_path)
        all_text = ""
        for sheet in xl.sheet_names[:5]:   # max 5 sheets
            df = xl.parse(sheet)
            df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
            all_text += f"\n--- Sheet: {sheet} ---\n"
            all_text += df.to_string(index=False) + "\n"
        return {"text": all_text, "structured": {}}
    except Exception as e:
        logger.error(f"Excel parse error: {e}")
        return {"text": "", "error": str(e)}


def _summarise_dataframe(df) -> str:
    """Generate a text summary of key numeric columns"""
    try:
        numeric = df.select_dtypes(include="number")
        if numeric.empty:
            return ""
        lines = ["STATISTICAL SUMMARY:"]
        for col in numeric.columns[:10]:
            lines.append(
                f"  {col}: min={numeric[col].min():.2f}, "
                f"max={numeric[col].max():.2f}, "
                f"mean={numeric[col].mean():.2f}"
            )
        return "\n".join(lines)
    except Exception:
        return ""


# ─────────────────────────────────────────────────────────────────────────────
# STRUCTURED DATA EXTRACTION  (regex + rule-based NLP)
# ─────────────────────────────────────────────────────────────────────────────

def _extract_structured(text: str, doc_type: str) -> Dict[str, Any]:
    """
    Extract key financial figures from text using regex patterns.
    Handles Indian number formats (crore, lakh, INR, Rs., ₹).
    """
    structured = {}

    def _find_number(patterns):
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                raw = m.group(1).replace(",", "").strip()
                try:
                    return float(raw)
                except ValueError:
                    continue
        return None

    # Revenue / Turnover
    rev = _find_number([
        r'(?:revenue|turnover|net sales)[^\d]{0,20}(?:INR|Rs\.?|₹)?\s*([\d,\.]+)\s*(?:crore|cr\.?)',
        r'(?:revenue|turnover|net sales)\s*[:\-]\s*([\d,\.]+)',
    ])
    if rev:
        structured["revenue_crore"] = rev

    # Net Profit / PAT
    pat = _find_number([
        r'(?:net profit|profit after tax|PAT)[^\d]{0,20}(?:INR|Rs\.?|₹)?\s*([\d,\.]+)',
    ])
    if pat:
        structured["net_profit_crore"] = pat

    # Total Debt / Borrowings
    debt = _find_number([
        r'(?:total debt|borrowings|total borrowing)[^\d]{0,20}(?:INR|Rs\.?|₹)?\s*([\d,\.]+)',
    ])
    if debt:
        structured["total_debt_crore"] = debt

    # EBITDA
    ebitda = _find_number([
        r'EBITDA[^\d]{0,20}(?:INR|Rs\.?|₹)?\s*([\d,\.]+)',
    ])
    if ebitda:
        structured["ebitda_crore"] = ebitda

    # Key ratios (already numeric in text)
    for label, key in [
        (r'current ratio', "current_ratio"),
        (r'debt.to.equity', "debt_to_equity"),
        (r'interest coverage', "interest_coverage"),
    ]:
        m = re.search(label + r'[:\s]+([\d\.]+)', text, re.IGNORECASE)
        if m:
            try:
                structured[key] = float(m.group(1))
            except ValueError:
                pass

    # GST mismatch
    m = re.search(r'(?:gstr.2a.*3b|mismatch)[^\d]{0,20}([\d\.]+)\s*%', text, re.IGNORECASE)
    if m:
        try:
            structured["gst_mismatch_pct"] = float(m.group(1))
        except ValueError:
            pass

    # Bounce rate
    m = re.search(r'bounce rate[:\s]+([\d\.]+)\s*%', text, re.IGNORECASE)
    if m:
        try:
            structured["bounce_rate_pct"] = float(m.group(1))
        except ValueError:
            pass

    return structured


# ─────────────────────────────────────────────────────────────────────────────
# MOCK DATA  (used when no real library is installed — demo mode)
# ─────────────────────────────────────────────────────────────────────────────

def _generate_mock_text(doc_type: str) -> str:
    """
    Realistic mock financial text used for demo when PDF libraries are absent.
    Replace with real document content once pip install PyMuPDF is done.
    """
    mocks = {
        "annual_report": """
ANNUAL REPORT 2023-24  [DEMO DATA — install PyMuPDF for real extraction]
Company: Sample Industries Ltd
Revenue: INR 450 Crore
Net Profit: INR 38 Crore
Total Debt: INR 120 Crore
EBITDA: INR 72 Crore
Current Ratio: 1.8
Debt-to-Equity: 0.65
Interest Coverage: 4.2x
Net Profit Margin: 8.4%
Revenue Growth: 12.3%
ROE: 18.5%
ROCE: 22.1%
Promoter Holding: 62% (stable)
The company has shown consistent revenue growth over 3 years.
Board approved greenfield expansion funded through internal accruals.
No major defaults or NPA classification in the past 5 years.
""",
        "gst": """
GST RETURN SUMMARY  [DEMO DATA]
Period: Q4 FY2023-24
Taxable Turnover: INR 112 Crore
Output GST: INR 20.16 Crore
Input Tax Credit (ITC): INR 18.2 Crore
Net Tax Paid: INR 1.96 Crore
GSTR-2A vs 3B Mismatch: 2.3% (within acceptable range)
ITC Utilisation: 90.3%
Filing Status: Compliant — all returns filed on time
E-Way Bill Count: 1,842 (consistent with declared turnover)
""",
        "bank_statement": """
BANK STATEMENT SUMMARY  [DEMO DATA]
Bank: HDFC Bank | Account Type: Current Account
Period: April 2023 — March 2024
Average Monthly Balance: INR 8.2 Crore
Total Credits (12 months): INR 98.5 Crore
Total Debits (12 months): INR 94.1 Crore
EMI Payments: Regular and on-time (0 missed)
Bounce Rate: 0.8% (Low — industry threshold: 3%)
Peak Debit: INR 12 Crore (Supplier payment — Apr 2023)
Inward RTGS/NEFT: 423 transactions
""",
        "csv": """
Financial Data CSV  [DEMO DATA]
Year, Revenue, PAT, Debt, EBITDA
2022, 380, 28, 100, 58
2023, 415, 34, 110, 65
2024, 450, 38, 120, 72
""",
        "other": "[DEMO DATA] Document uploaded. Install PyMuPDF for real text extraction.",
    }
    return mocks.get(doc_type, mocks["other"])
