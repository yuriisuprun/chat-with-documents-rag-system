"""
Deep dive into the memoryview/read error and requests library behavior.

Key findings from the initial tests:
- Raw bytes: Causes READ TIMEOUT (server doesn't respond)
- BytesIO: Works fine
- File-like objects: Work fine
- Memoryview: Surprisingly works with requests!

This script will:
1. Investigate why raw bytes cause timeout
2. Trace through requests' multipart encoding to find where memoryview error comes from
3. Test with real Streamlit UploadedFile if possible
"""

import io
import logging
import sys
import traceback
from pathlib import Path
from typing import Any

import requests

# Setup detailed logging with file output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("debug_deep_dive.log"),
    ]
)
logger = logging.getLogger(__name__)

# Also log requests library internals
logging.getLogger("urllib3").setLevel(logging.DEBUG)
logging.getLogger("requests").setLevel(logging.DEBUG)

TEST_PDF_PATH = Path("test_document.pdf")


def create_test_pdf():
    """Create a minimal valid PDF."""
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 612 792] /Contents 5 0 obj >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Test Document) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000000333 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
428
%%EOF"""
    
    TEST_PDF_PATH.write_bytes(pdf_content)
    logger.info(f"Created test PDF: {len(pdf_content)} bytes")
    return pdf_content


def inspect_multipart_encoding():
    """Inspect how requests encodes multipart data for different input types."""
    logger.info("\n" + "="*80)
    logger.info("INSPECTION: How requests encodes multipart for different types")
    logger.info("="*80)
    
    pdf_content = create_test_pdf()
    
    # Monkey-patch requests' multipart encoder to trace what it does
    from requests_toolbelt import MultipartEncoder
    from requests import adapters
    
    original_send = adapters.HTTPAdapter.send
    
    def traced_send(self, request, **kwargs):
        logger.info(f"\n>>> HTTPAdapter.send() called")
        logger.info(f"    Request method: {request.method}")
        logger.info(f"    Request URL: {request.url}")
        logger.info(f"    Request headers: {dict(request.headers)}")
        
        if request.body:
            body_type = type(request.body)
            logger.info(f"    Request body type: {body_type}")
            
            if hasattr(request.body, '__len__'):
                body_len = len(request.body)
                logger.info(f"    Request body length: {body_len}")
            
            if hasattr(request.body, 'read'):
                logger.info(f"    Request body is file-like, has .read()")
            
        # Call original
        try:
            result = original_send(self, request, **kwargs)
            logger.info(f"<<< Response: {result.status_code}")
            return result
        except Exception as e:
            logger.error(f"<<< Exception: {type(e).__name__}: {e}")
            raise
    
    adapters.HTTPAdapter.send = traced_send
    
    tests = [
        ("Raw bytes", ("test.pdf", pdf_content, "application/pdf")),
        ("BytesIO", ("test.pdf", io.BytesIO(pdf_content), "application/pdf")),
        ("Memoryview", ("test.pdf", memoryview(pdf_content), "application/pdf")),
    ]
    
    for test_name, file_tuple in tests:
        logger.info(f"\n--- Test: {test_name} ---")
        try:
            files = {"file": file_tuple}
            logger.info(f"Making request with {test_name}...")
            response = requests.post(
                "http://localhost:8000/api/v1/documents/upload",
                files=files,
                timeout=10
            )
            logger.info(f"✓ Success: {response.status_code}")
        except Exception as e:
            logger.error(f"✗ Error: {type(e).__name__}: {e}")
            traceback.print_exc()


def test_with_real_streamlit():
    """Try to import and test with real Streamlit UploadedFile."""
    logger.info("\n" + "="*80)
    logger.info("TEST: Real Streamlit UploadedFile")
    logger.info("="*80)
    
    try:
        import streamlit as st
        logger.info("✓ Streamlit imported")
        
        # Streamlit UploadedFile is a BytesIO subclass
        logger.info("Streamlit UploadedFile class hierarchy:")
        logger.info(f"  Base classes: {st.UploadedFile.__bases__}")
        
        pdf_content = create_test_pdf()
        
        # Create a mock UploadedFile
        uploaded_file = st.UploadedFile(
            name="test.pdf",
            data=io.BytesIO(pdf_content),
            type="application/pdf"
        )
        logger.info(f"Created Streamlit UploadedFile: {type(uploaded_file)}")
        
        # Test upload
        files = {"file": ("test.pdf", uploaded_file, "application/pdf")}
        logger.info("Making request with Streamlit UploadedFile...")
        response = requests.post(
            "http://localhost:8000/api/v1/documents/upload",
            files=files,
            timeout=10
        )
        logger.info(f"✓ Success: {response.status_code}")
        
    except ImportError:
        logger.warning("Streamlit not available in test environment")
    except Exception as e:
        logger.error(f"Error: {type(e).__name__}: {e}")
        traceback.print_exc()


def test_requests_file_reading_logic():
    """
    Test the exact code path requests uses to read files.
    
    In requests.models.RequestEncodingMixin, multipart encoding does:
    for k, v in files.items():
        if isinstance(v, (tuple, list)):
            v = v  # filename, file-like, content-type
        
        if hasattr(v[1], 'read'):
            v[1].read()  # <-- This is where memoryview might fail
    """
    logger.info("\n" + "="*80)
    logger.info("TEST: Requests file reading logic simulation")
    logger.info("="*80)
    
    pdf_content = create_test_pdf()
    
    test_cases = [
        ("bytes", pdf_content),
        ("BytesIO", io.BytesIO(pdf_content)),
        ("memoryview", memoryview(pdf_content)),
    ]
    
    for test_name, content in test_cases:
        logger.info(f"\n--- {test_name} ---")
        logger.info(f"Type: {type(content)}")
        logger.info(f"Has .read(): {hasattr(content, 'read')}")
        
        if hasattr(content, 'read'):
            logger.info("Calling .read()...")
            try:
                result = content.read()
                logger.info(f"✓ .read() successful, returned {type(result)}")
            except AttributeError as e:
                logger.error(f"✗ .read() FAILED: {e}")
        else:
            logger.info("No .read() method, requests won't call it")


def debug_raw_bytes_timeout():
    """
    Investigate why raw bytes causes timeout instead of memoryview error.
    
    Hypothesis: When request.body is raw bytes (not file-like),
    requests handles it differently and maybe the server expects
    streaming/chunked encoding?
    """
    logger.info("\n" + "="*80)
    logger.info("DEBUG: Why raw bytes cause timeout?")
    logger.info("="*80)
    
    from requests import Request, Session
    from requests.structures import CaseInsensitiveDict
    
    pdf_content = create_test_pdf()
    
    # Manually prepare requests the way requests library does
    test_cases = [
        ("bytes", pdf_content),
        ("BytesIO", io.BytesIO(pdf_content)),
    ]
    
    for test_name, file_content in test_cases:
        logger.info(f"\n--- Preparing request with {test_name} ---")
        
        req = Request(
            'POST',
            'http://localhost:8000/api/v1/documents/upload',
            files={'file': ('test.pdf', file_content, 'application/pdf')}
        )
        
        prepared = req.prepare()
        logger.info(f"Prepared request body type: {type(prepared.body)}")
        
        if hasattr(prepared.body, '__len__'):
            logger.info(f"Body length: {len(prepared.body)} bytes")
        
        if hasattr(prepared.body, 'read'):
            logger.info("Body is file-like (has .read())")
        else:
            logger.info("Body is NOT file-like (no .read())")
        
        logger.info(f"Headers:")
        for k, v in prepared.headers.items():
            logger.info(f"  {k}: {v}")


def main():
    logger.info("="*80)
    logger.info("DEEP DIVE: Memoryview and raw bytes issues")
    logger.info("="*80)
    
    # Check backend
    try:
        logger.info("\nChecking backend...")
        response = requests.get("http://localhost:8000/api/v1/health", timeout=2)
        logger.info(f"✓ Backend running: {response.status_code}")
    except Exception as e:
        logger.error(f"✗ Backend not running: {e}")
        return
    
    # Run all investigations
    test_requests_file_reading_logic()
    debug_raw_bytes_timeout()
    inspect_multipart_encoding()
    test_with_real_streamlit()
    
    # Cleanup
    if TEST_PDF_PATH.exists():
        TEST_PDF_PATH.unlink()
    
    logger.info("\n" + "="*80)
    logger.info("Full debug log saved to: debug_deep_dive.log")
    logger.info("="*80)


if __name__ == "__main__":
    main()
