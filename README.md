# 🪪 DocuID Pro — AI Identity Document Identification & Intelligence Suite

An intelligent, production-ready application that classifies, extracts structured data from, and automatically organizes Indian and international identity documents (PDFs, Images, and Word DOCX).

Revived and modernized from legacy Google Colab notebooks into a high-performance, attractive desktop & web application with zero external binary installation requirements.

---

## ✨ Features & Capabilities

- 📄 **Universal Document Ingestion**:
  - **Multi-page PDFs**: Automatically splits multi-page PDF documents into individual pages.
  - **Scanned Images**: JPG, JPEG, PNG, WEBP, BMP, TIFF.
  - **Word Documents**: `.docx` documents parsed directly.
- 🧠 **Embedded Deep Learning OCR**:
  - Powered by **RapidOCR (ONNX Runtime)** + **PyMuPDF**.
  - Runs 100% locally on CPU without needing manual `tesseract.exe` or `poppler-utils` installations on Windows!
  - High accuracy text detection even on tilted, low-resolution, or noisy scans.
- 🎯 **10 Supported Document Categories**:
  1. **Aadhaar Card** *(UIDAI, Enrollment No, 12-digit Aadhaar pattern)*
  2. **PAN Card** *(Income Tax Department, Permanent Account Number pattern)*
  3. **Driving License** *(Motor Driving Licence, Transport Department, DL No)*
  4. **Voter ID Card** *(Election Commission of India, EPIC Card Number)*
  5. **Passport** *(Republic of India, MRZ Code parsing)*
  6. **Salary Slip / Payslip** *(Earnings, Net Pay, Deductions, Pay Period)*
  7. **Form 16** *(TDS Certificate under Section 203, TRACES, Assessment Year)*
  8. **Bank Statement** *(Account Holder, Statement Period, Ledger, Balances)*
  9. **Bank Cheque** *(Payee Name, IFSC Code, Account Payee, Cheque Amount)*
  10. **Utility Bill** *(Water Authority / Electricity, Consumer ID, Due Dates)*
- 🔍 **Structured Entity Extraction**:
  - Automatically extracts: Full Name, Document ID Number, DOB / Issue / Expiry Dates, Gender, Father/Relation Name, Financial Amounts, Authority / Provider.
- 🎨 **Modern Interactive UI**:
  - Sleek glassmorphism dark-mode UI with live metrics and responsive design.
  - Category filter pills with real-time counters and instant text search.
  - Detailed Document Inspector modal with high-res document viewer.
  - 1-Click Copy-to-Clipboard for each extracted field.
- 📁 **Automated Organization & Export**:
  - **Download Organized ZIP**: Automatically sorts pages into folders (`aadhar/`, `pan/`, `salary/`, etc.) containing images, text dumps, and a summary CSV.
  - **CSV / JSON Reports**: Instant export of extracted data.
- ⚡ **1-Click Sample Showcase**:
  - Click **"Try Sample (10 Docs)"** to instantly run the embedded `documents.pdf` sample dataset and watch all 10 document types get identified in seconds!

---

## 🚀 Quick Start (Windows)

### Option 1: 1-Click Double-Click Launcher (Recommended)
Simply double-click the **`run_app.bat`** file in this folder:
```cmd
run_app.bat
```
This will automatically launch the server and open your default browser at `http://127.0.0.1:8000`.

---

### Option 2: Run with UV (Blazing Fast)
If you have `uv` installed:
```bash
uv run --with fastapi --with uvicorn --with pymupdf --with rapidocr-onnxruntime --with python-docx --with python-multipart python run.py
```

---

### Option 3: Standard Python / Pip
1. Install dependencies:
```bash
pip install -r requirements.txt
```
2. Start the application:
```bash
python run.py
```
3. Open `http://127.0.0.1:8000` in your browser.

---

## 🏗️ Project Structure

```
Documents-Identification-main/
│
├── run_app.bat               # 1-click Windows desktop launcher
├── run.py                    # App launcher with automatic browser opening
├── app.py                    # FastAPI server & REST API
├── requirements.txt          # Python dependencies
├── documents.pdf             # 10-page sample identity document dataset
│
├── engine/                   # Core Document Processing Engine
│   ├── __init__.py
│   ├── ocr.py                # PyMuPDF rendering & ONNX Deep OCR engine
│   ├── classifier.py         # Multi-signal weighted classification logic
│   └── extractor.py          # Category-specific structured entity extractors
│
├── static/                   # Modern Web Application Frontend
│   └── index.html            # Tailwind CSS + Lucide Icons interactive UI
│
├── Classify.ipynb            # (Legacy) Original Google Colab notebook
├── Extract.ipynb             # (Legacy) Original Google Colab notebook
└── main.ipynb                # (Legacy) Original Google Colab notebook
```

---

## 🔌 API Endpoints

- `GET /` — Serves the interactive Web Application.
- `POST /api/upload` — Upload one or multiple documents (PDF, Images, DOCX).
- `POST /api/sample` — 1-Click execution on the included `documents.pdf` dataset.
- `GET /api/preview/{item_id}` — High-resolution preview image of any document page.
- `GET /api/stats` — Overall statistics (totals, identified counts, accuracy).
- `GET /api/download-zip` — Download categorized ZIP archive sorted into category folders.
- `GET /api/export-csv` — Export all processed data as CSV.
- `GET /api/export-json` — Full JSON structured export.
- `POST /api/clear` — Clear current session items.
