@echo off
title DocuID Pro - AI Document Identification
color 0b

echo ========================================================
echo         DocuID Pro - Identity Documents Identification  
echo ========================================================
echo.
echo Initializing AI OCR Engine and Web Application...
echo.

where uv >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Using uv package runner...
    uv run --with fastapi --with uvicorn --with pymupdf --with rapidocr-onnxruntime --with python-docx --with python-multipart python run.py
    goto end
)

if exist "%USERPROFILE%\.local\bin\uv.exe" (
    echo Using uv from %USERPROFILE%\.local\bin\uv.exe...
    "%USERPROFILE%\.local\bin\uv.exe" run --with fastapi --with uvicorn --with pymupdf --with rapidocr-onnxruntime --with python-docx --with python-multipart python run.py
    goto end
)

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Using system Python...
    python run.py
    goto end
)

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Using Python Launcher py...
    py run.py
    goto end
)

echo [ERROR] Neither uv nor Python was found on your PATH.
echo Please ensure Python or uv is installed to run the application.
pause

:end

