#!/usr/bin/env python
"""Test PDF extraction fix."""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.infrastructure.pdf.extractor import PDFExtractor

# Find a test PDF
test_pdf = Path(__file__).parent / "test_document.pdf"

if test_pdf.exists():
    print(f"Testing PDF extraction with: {test_pdf}")
    extractor = PDFExtractor()
    try:
        result = extractor.extract_text(test_pdf)
        print(f"✓ PDF extraction successful!")
        print(f"  Pages: {result['page_count']}")
        print(f"  Total text length: {result['total_text_length']} chars")
        print(f"  Has extractable text: {result['has_extractable_text']}")
    except Exception as e:
        print(f"✗ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"Test PDF not found at {test_pdf}")
    print("Creating a minimal test to verify fitz import...")
    try:
        import pymupdf as fitz
        print(f"✓ PyMuPDF import successful (version {fitz.__version__})")
    except ImportError as e:
        print(f"✗ PyMuPDF import failed: {e}")
        try:
            import fitz
            print(f"✓ fitz import successful (version {fitz.__version__})")
        except ImportError as e2:
            print(f"✗ fitz import failed: {e2}")
