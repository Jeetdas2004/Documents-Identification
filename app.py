import os
import io
import uuid
import zipfile
import csv
import base64
from typing import List, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from engine.ocr import process_file_to_pages
from engine.classifier import classify_text, DOCUMENT_PROFILES
from engine.extractor import extract_document_fields

app = FastAPI(title="DocuID Intelligence Pro", version="2.0.0")

# In-memory document storage for session
PROCESSED_DOCUMENTS: Dict[str, Dict[str, Any]] = {}
PAGE_IMAGES: Dict[str, bytes] = {}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
if not os.path.exists(STATIC_DIR):
    # Fallback to current working directory or relative static
    alt_static = os.path.join(os.getcwd(), "static")
    if os.path.exists(alt_static):
        STATIC_DIR = alt_static
    else:
        os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(index_path):
        alt_path = os.path.join(os.getcwd(), "static", "index.html")
        if os.path.exists(alt_path):
            index_path = alt_path
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>DocuID AI Application Backend Active. Static frontend initializing...</h1>"

@app.get("/api/stats")
async def get_stats():
    docs = list(PROCESSED_DOCUMENTS.values())
    total = len(docs)
    classified_count = sum(1 for d in docs if d["classification"]["type"] != "unknown")
    avg_conf = int(sum(d["classification"]["confidence"] for d in docs) / total) if total > 0 else 0
    
    categories = {}
    for d in docs:
        t = d["classification"]["type"]
        categories[t] = categories.get(t, 0) + 1
        
    return {
        "total": total,
        "classified": classified_count,
        "average_confidence": avg_conf,
        "categories": categories
    }

def process_and_register_pages(pages: List[Dict[str, Any]], original_filename: str) -> List[Dict[str, Any]]:
    results = []
    total_pages = len(pages)
    
    for page in pages:
        item_id = str(uuid.uuid4())
        page_num = page["page_number"]
        text = page["text"]
        lines = [l["text"] for l in page.get("lines", [])]
        
        # Classification & Extraction
        classification = classify_text(text)
        fields = extract_document_fields(classification["type"], text, lines)
        
        # Save image for preview
        img_bytes = page.get("image_bytes", b"")
        PAGE_IMAGES[item_id] = img_bytes
        
        # Generate base64 thumbnail for serverless persistence
        image_data = ""
        if img_bytes:
            image_data = f"data:image/jpeg;base64,{base64.b64encode(img_bytes).decode('utf-8')}"
            # Also write to temporary directory as file cache if supported
            try:
                tmp_dir = os.environ.get("TMPDIR", "/tmp")
                if os.path.exists(tmp_dir) and os.path.isdir(tmp_dir):
                    with open(os.path.join(tmp_dir, f"doc_{item_id}.jpg"), "wb") as f_tmp:
                        f_tmp.write(img_bytes)
            except Exception:
                pass
        
        doc_record = {
            "id": item_id,
            "filename": original_filename,
            "page_number": page_num,
            "total_pages": total_pages,
            "classification": classification,
            "fields": fields,
            "text_preview": text[:250].replace("\n", " ").strip() if text else "No text detected",
            "text_full": text,
            "source": page.get("source", "ocr"),
            "image_data": image_data
        }
        
        PROCESSED_DOCUMENTS[item_id] = doc_record
        results.append(doc_record)
        
    return results

@app.post("/api/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")
        
    all_results = []
    for f in files:
        content = await f.read()
        pages = process_file_to_pages(file_bytes=content, filename=f.filename)
        registered = process_and_register_pages(pages, f.filename)
        all_results.extend(registered)
        
    return {"status": "success", "processed_count": len(all_results), "items": all_results}

@app.post("/api/sample")
async def process_sample_dataset():
    sample_path = os.path.join(BASE_DIR, "documents.pdf")
    if not os.path.exists(sample_path):
        alt_sample = os.path.join(os.getcwd(), "documents.pdf")
        if os.path.exists(alt_sample):
            sample_path = alt_sample
        else:
            raise HTTPException(status_code=404, detail="documents.pdf not found in project directory.")
        
    with open(sample_path, "rb") as f:
        content = f.read()
        
    pages = process_file_to_pages(file_bytes=content, filename="documents.pdf")
    registered = process_and_register_pages(pages, "documents.pdf")
    return {"status": "success", "processed_count": len(registered), "items": registered}

@app.get("/api/preview/{item_id}")
async def get_document_preview(item_id: str):
    if item_id in PAGE_IMAGES:
        return Response(content=PAGE_IMAGES[item_id], media_type="image/jpeg")
    
    # Check /tmp directory fallback
    tmp_dir = os.environ.get("TMPDIR", "/tmp")
    tmp_file = os.path.join(tmp_dir, f"doc_{item_id}.jpg")
    if os.path.exists(tmp_file):
        with open(tmp_file, "rb") as f:
            return Response(content=f.read(), media_type="image/jpeg")
            
    raise HTTPException(status_code=404, detail="Preview image not found.")

class UpdateFieldRequest(BaseModel):
    item_id: str
    fields: Dict[str, Any]

@app.post("/api/update-fields")
async def update_fields(req: UpdateFieldRequest):
    if req.item_id not in PROCESSED_DOCUMENTS:
        raise HTTPException(status_code=404, detail="Item not found.")
    PROCESSED_DOCUMENTS[req.item_id]["fields"] = req.fields
    return {"status": "success", "item": PROCESSED_DOCUMENTS[req.item_id]}

@app.post("/api/clear")
async def clear_all():
    PROCESSED_DOCUMENTS.clear()
    PAGE_IMAGES.clear()
    return {"status": "success", "message": "All documents cleared."}

@app.get("/api/export-csv")
async def export_csv():
    docs = list(PROCESSED_DOCUMENTS.values())
    if not docs:
        raise HTTPException(status_code=400, detail="No processed documents available to export.")
        
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Item ID", "Filename", "Page", "Document Type", "Confidence (%)", "Extracted Fields", "Raw OCR Excerpt"])
    
    for d in docs:
        c = d["classification"]
        fields_str = "; ".join([f"{k}: {v}" for k, v in d["fields"].items()])
        writer.writerow([
            d["id"],
            d["filename"],
            d["page_number"],
            c["title"],
            c["confidence"],
            fields_str,
            d["text_preview"]
        ])
        
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=classified_documents_report.csv"}
    )

@app.get("/api/export-json")
async def export_json():
    return list(PROCESSED_DOCUMENTS.values())

@app.get("/api/download-zip")
async def download_organized_zip():
    docs = list(PROCESSED_DOCUMENTS.values())
    if not docs:
        raise HTTPException(status_code=400, detail="No processed documents to organize.")
        
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        summary_rows = [["Filename", "Page", "Category", "Confidence", "Extracted Fields"]]
        
        for d in docs:
            item_id = d["id"]
            cat_folder = d["classification"]["type"]
            page_num = d["page_number"]
            base_fname = os.path.splitext(d["filename"])[0]
            
            # Save page image
            img_bytes = PAGE_IMAGES.get(item_id)
            if img_bytes:
                img_path = f"{cat_folder}/{base_fname}_page{page_num}.jpg"
                zip_file.writestr(img_path, img_bytes)
                
            # Save page metadata
            meta_path = f"{cat_folder}/{base_fname}_page{page_num}_info.txt"
            info_txt = f"Document Category: {d['classification']['title']}\n"
            info_txt += f"Confidence Score: {d['classification']['confidence']}%\n"
            info_txt += f"Source File: {d['filename']} (Page {page_num})\n\n"
            info_txt += "--- EXTRACTED FIELDS ---\n"
            for k, v in d["fields"].items():
                info_txt += f"{k}: {v}\n"
            info_txt += "\n--- DETECTED TEXT ---\n"
            info_txt += d["text_full"]
            zip_file.writestr(meta_path, info_txt)
            
            fields_str = "; ".join([f"{k}: {v}" for k, v in d["fields"].items()])
            summary_rows.append([d["filename"], str(page_num), d["classification"]["title"], f"{d['classification']['confidence']}%", fields_str])
            
        # Add summary CSV to root of zip
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerows(summary_rows)
        zip_file.writestr("summary_report.csv", csv_buffer.getvalue())
        
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=classified_documents_archive.zip"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

