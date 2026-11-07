import io
import os
import fitz  # PyMuPDF
from PIL import Image
from typing import List, Dict, Any

_rapid_ocr_instance = None

def get_ocr_engine():
    global _rapid_ocr_instance
    if _rapid_ocr_instance is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
            _rapid_ocr_instance = RapidOCR()
        except Exception as e:
            print(f"[Warning] RapidOCR could not be initialized (serverless/constrained environment): {e}")
            _rapid_ocr_instance = False
    return _rapid_ocr_instance

def run_ocr_on_image_bytes(image_bytes: bytes) -> Dict[str, Any]:
    """Runs RapidOCR on image bytes and returns concatenated text and detected lines."""
    engine = get_ocr_engine()
    if not engine:
        return {
            "text": "Image uploaded. Running in serverless demo mode.",
            "lines": [],
            "elapse": []
        }
        
    try:
        result, elapse = engine(image_bytes)
    except Exception as e:
        print(f"[Error] OCR processing failed on page image: {e}")
        result, elapse = None, []
        
    lines = []
    text_parts = []
    
    if result:
        for item in result:
            bbox = item[0]
            line_text = item[1].strip()
            score = float(item[2])
            if line_text:
                lines.append({"text": line_text, "score": score, "bbox": bbox})
                text_parts.append(line_text)
                
    full_text = "\n".join(text_parts)
    return {
        "text": full_text,
        "lines": lines,
        "elapse": elapse if elapse else []
    }

def process_file_to_pages(file_path: str = None, file_bytes: bytes = None, filename: str = "") -> List[Dict[str, Any]]:
    """
    Extracts pages from PDF, Image, or Word docx.
    Returns list of dicts:
    [
      {
        "page_number": int,
        "image_bytes": bytes (JPEG preview),
        "text": str,
        "lines": list,
        "source": str
      }
    ]
    """
    ext = os.path.splitext(filename.lower())[1]
    pages_output = []
    
    # 1. Handle PDF
    if ext == ".pdf" or (file_bytes and file_bytes[:4] == b"%PDF"):
        if file_bytes:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        else:
            doc = fitz.open(file_path)
            
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("jpeg")
            
            # Check embedded text first
            embedded_text = page.get_text().strip()
            
            if len(embedded_text) > 80:
                # Digital PDF with rich selectable text
                pages_output.append({
                    "page_number": i + 1,
                    "image_bytes": img_bytes,
                    "text": embedded_text,
                    "lines": [{"text": line, "score": 1.0} for line in embedded_text.splitlines() if line.strip()],
                    "source": "embedded_pdf_text"
                })
            else:
                # Scanned page - use OCR
                ocr_res = run_ocr_on_image_bytes(img_bytes)
                pages_output.append({
                    "page_number": i + 1,
                    "image_bytes": img_bytes,
                    "text": ocr_res["text"],
                    "lines": ocr_res["lines"],
                    "source": "ocr_onnx"
                })
        doc.close()
        
    # 2. Handle DOCX
    elif ext in [".docx", ".doc"]:
        import docx
        if file_bytes:
            doc = docx.Document(io.BytesIO(file_bytes))
        else:
            doc = docx.Document(file_path)
            
        full_text = []
        for p in doc.paragraphs:
            if p.text.strip():
                full_text.append(p.text.strip())
        for table in doc.tables:
            for row in table.rows:
                row_txt = " | ".join([c.text.strip() for c in row.cells if c.text.strip()])
                if row_txt:
                    full_text.append(row_txt)
                    
        combined_text = "\n".join(full_text)
        
        # Create a synthetic image banner for Word docs
        blank_img = Image.new("RGB", (600, 800), color=(255, 255, 255))
        buf = io.BytesIO()
        blank_img.save(buf, format="JPEG")
        
        pages_output.append({
            "page_number": 1,
            "image_bytes": buf.getvalue(),
            "text": combined_text,
            "lines": [{"text": l, "score": 1.0} for l in full_text],
            "source": "docx_text"
        })
        
    # 3. Handle Standard Image files (PNG, JPG, JPEG, WEBP, BMP, TIFF)
    else:
        if file_bytes:
            img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        else:
            img = Image.open(file_path).convert("RGB")
            
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        img_bytes = buf.getvalue()
        
        ocr_res = run_ocr_on_image_bytes(img_bytes)
        pages_output.append({
            "page_number": 1,
            "image_bytes": img_bytes,
            "text": ocr_res["text"],
            "lines": ocr_res["lines"],
            "source": "ocr_onnx"
        })
        
    return pages_output

