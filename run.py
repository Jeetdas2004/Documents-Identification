import os
import sys
import time
import threading
import webbrowser
import uvicorn

def open_browser():
    time.sleep(1.5)
    print("Launching browser at http://127.0.0.1:8000 ...")
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    print("=======================================================")
    print("      DocuID Pro - AI Document Identification Suite    ")
    print("=======================================================")
    print("Starting server at http://127.0.0.1:8000 ...")
    
    # Open browser automatically in a separate thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run the FastAPI server
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)

