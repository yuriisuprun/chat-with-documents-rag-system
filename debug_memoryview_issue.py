"""
Comprehensive debugging script for memoryview "has no attribute read" error.

Tests multiple approaches:
1. Raw bytes in files dict
2. BytesIO wrapper
3. urllib3 directly
4. Simulating Streamlit UploadedFile behavior
5. curl subprocess call
"""

import io
import logging
import sys
import traceback
from pathlib import Path
from typing import Any

import requests
import urllib3

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create test PDF
TEST_PDF_PATH = Path("test_document.pdf")


def create_test_pdf():
    """Create a minimal valid PDF for testing."""
    logger.info("Creating test PDF...")
    
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 612 792] /Contents 5 0 R >>
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
    logger.info(f"Created test PDF at {TEST_PDF_PATH} ({len(pdf_content)} bytes)")
    return pdf_content


class FakeStreamlitUploadedFile:
    """Simulates Streamlit's UploadedFile behavior."""
    
    def __init__(self, content: bytes, name: str):
        self.content = content
        self.name = name
        self._file = io.BytesIO(content)
        self.size = len(content)
        
    def read(self, size: int = -1):
        logger.debug(f"FakeStreamlitUploadedFile.read({size}) called")
        result = self._file.read(size)
        logger.debug(f"read() returning type: {type(result)}, len: {len(result) if hasattr(result, '__len__') else 'N/A'}")
        return result
    
    def seek(self, offset: int):
        logger.debug(f"FakeStreamlitUploadedFile.seek({offset}) called")
        return self._file.seek(offset)
    
    def getvalue(self):
        logger.debug("FakeStreamlitUploadedFile.getvalue() called")
        result = self._file.getvalue()
        logger.debug(f"getvalue() returning type: {type(result)}")
        return result


def test_approach_1_raw_bytes():
    """Test 1: Raw bytes in files dict."""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Raw bytes in files dict")
    logger.info("="*80)
    
    try:
        pdf_content = create_test_pdf()
        
        logger.debug("Creating files dict with raw bytes...")
        files = {
            "file": ("test.pdf", pdf_content, "application/pdf")
        }
        logger.debug(f"Files dict: file[0]={files['file'][0]}, file[1] type={type(files['file'][1])}, file[2]={files['file'][2]}")
        
        # Try to inspect what requests will do internally
        logger.debug("Attempting POST request...")
        response = requests.post(
            "http://localhost:8000/api/v1/documents/upload",
            files=files,
            timeout=5
        )
        logger.info(f"✓ SUCCESS: Status {response.status_code}")
        logger.debug(f"Response: {response.text[:200]}")
        return True
        
    except AttributeError as e:
        if "memoryview" in str(e) or "read" in str(e):
            logger.error(f"✗ MEMORYVIEW ERROR (as expected): {e}")
            traceback.print_exc()
            return False
        raise
    except Exception as e:
        logger.error(f"✗ UNEXPECTED ERROR: {type(e).__name__}: {e}")
        traceback.print_exc()
        return False


def test_approach_2_bytesio():
    """Test 2: BytesIO wrapper."""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: BytesIO wrapper")
    logger.info("="*80)
    
    try:
        pdf_content = create_test_pdf()
        
        logger.debug("Creating BytesIO wrapper...")
        file_obj = io.BytesIO(pdf_content)
        logger.debug(f"BytesIO object type: {type(file_obj)}")
        
        files = {
            "file": ("test.pdf", file_obj, "application/pdf")
        }
        logger.debug("Files dict created")
        
        logger.debug("Attempting POST request...")
        response = requests.post(
            "http://localhost:8000/api/v1/documents/upload",
            files=files,
            timeout=5
        )
        logger.info(f"✓ SUCCESS: Status {response.status_code}")
        logger.debug(f"Response: {response.text[:200]}")
        return True
        
    except AttributeError as e:
        if "memoryview" in str(e) or "read" in str(e):
            logger.error(f"✗ MEMORYVIEW ERROR: {e}")
            traceback.print_exc()
            return False
        raise
    except Exception as e:
        logger.error(f"✗ UNEXPECTED ERROR: {type(e).__name__}: {e}")
        traceback.print_exc()
        return False


def test_approach_3_fake_streamlit():
    """Test 3: Fake Streamlit UploadedFile (returns bytes from read())."""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: Fake Streamlit UploadedFile (read returns bytes)")
    logger.info("="*80)
    
    try:
        pdf_content = create_test_pdf()
        
        logger.debug("Creating fake Streamlit UploadedFile...")
        file_obj = FakeStreamlitUploadedFile(pdf_content, "test.pdf")
        logger.debug(f"File object type: {type(file_obj)}")
        
        files = {
            "file": ("test.pdf", file_obj, "application/pdf")
        }
        logger.debug("Files dict created with UploadedFile object")
        
        logger.debug("Attempting POST request...")
        response = requests.post(
            "http://localhost:8000/api/v1/documents/upload",
            files=files,
            timeout=5
        )
        logger.info(f"✓ SUCCESS: Status {response.status_code}")
        logger.debug(f"Response: {response.text[:200]}")
        return True
        
    except AttributeError as e:
        if "memoryview" in str(e) or "read" in str(e):
            logger.error(f"✗ MEMORYVIEW ERROR: {e}")
            logger.error("Full traceback:")
            traceback.print_exc()
            return False
        raise
    except Exception as e:
        logger.error(f"✗ UNEXPECTED ERROR: {type(e).__name__}: {e}")
        traceback.print_exc()
        return False


def test_approach_4_fake_streamlit_getvalue():
    """Test 4: Fake Streamlit UploadedFile (using getvalue preconversion)."""
    logger.info("\n" + "="*80)
    logger.info("TEST 4: Fake Streamlit UploadedFile (convert with getvalue)")
    logger.info("="*80)
    
    try:
        pdf_content = create_test_pdf()
        
        logger.debug("Creating fake Streamlit UploadedFile...")
        file_obj = FakeStreamlitUploadedFile(pdf_content, "test.pdf")
        
        logger.debug("Pre-converting content to bytes using getvalue()...")
        content = file_obj.getvalue()
        logger.debug(f"Content type after getvalue(): {type(content)}")
        
        if isinstance(content, memoryview):
            logger.debug("Converting memoryview to bytes...")
            content = bytes(content)
        
        files = {
            "file": ("test.pdf", content, "application/pdf")
        }
        logger.debug("Files dict created with raw bytes")
        
        logger.debug("Attempting POST request...")
        response = requests.post(
            "http://localhost:8000/api/v1/documents/upload",
            files=files,
            timeout=5
        )
        logger.info(f"✓ SUCCESS: Status {response.status_code}")
        logger.debug(f"Response: {response.text[:200]}")
        return True
        
    except AttributeError as e:
        if "memoryview" in str(e) or "read" in str(e):
            logger.error(f"✗ MEMORYVIEW ERROR: {e}")
            traceback.print_exc()
            return False
        raise
    except Exception as e:
        logger.error(f"✗ UNEXPECTED ERROR: {type(e).__name__}: {e}")
        traceback.print_exc()
        return False


def test_approach_5_urllib3_directly():
    """Test 5: Using urllib3 directly (lower level)."""
    logger.info("\n" + "="*80)
    logger.info("TEST 5: urllib3 direct connection")
    logger.info("="*80)
    
    try:
        pdf_content = create_test_pdf()
        
        logger.debug("Creating urllib3 PoolManager...")
        http = urllib3.PoolManager()
        
        logger.debug("Creating multipart fields...")
        fields = {
            "file": ("test.pdf", pdf_content, "application/pdf"),
        }
        
        logger.debug("Attempting urllib3 POST request...")
        response = http.request_encode_multipart(
            'POST',
            'http://localhost:8000/api/v1/documents/upload',
            fields=fields
        )
        logger.info(f"✓ SUCCESS: Status {response.status}")
        logger.debug(f"Response: {response.data[:200]}")
        return True
        
    except AttributeError as e:
        if "memoryview" in str(e) or "read" in str(e):
            logger.error(f"✗ MEMORYVIEW ERROR: {e}")
            traceback.print_exc()
            return False
        raise
    except Exception as e:
        logger.error(f"✗ UNEXPECTED ERROR: {type(e).__name__}: {e}")
        traceback.print_exc()
        return False


def test_approach_6_memoryview_directly():
    """Test 6: Explicitly pass memoryview to see the error."""
    logger.info("\n" + "="*80)
    logger.info("TEST 6: Memoryview object directly (to trigger error)")
    logger.info("="*80)
    
    try:
        pdf_content = create_test_pdf()
        
        logger.debug("Creating memoryview from bytes...")
        mv_content = memoryview(pdf_content)
        logger.debug(f"Memoryview type: {type(mv_content)}")
        logger.debug(f"Memoryview has read(): {hasattr(mv_content, 'read')}")
        
        files = {
            "file": ("test.pdf", mv_content, "application/pdf")
        }
        
        logger.debug("Attempting POST request with memoryview...")
        response = requests.post(
            "http://localhost:8000/api/v1/documents/upload",
            files=files,
            timeout=5
        )
        logger.info(f"Status {response.status_code}")
        return True
        
    except AttributeError as e:
        if "memoryview" in str(e) or "read" in str(e):
            logger.error(f"✓ CAUGHT EXPECTED ERROR: {e}")
            logger.error("This is the error we're looking for!")
            traceback.print_exc()
            return False
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {type(e).__name__}: {e}")
        traceback.print_exc()
        return False


def inspect_requests_internals():
    """Inspect how requests handles different file types."""
    logger.info("\n" + "="*80)
    logger.info("INSPECTION: requests library internals")
    logger.info("="*80)
    
    try:
        from requests_toolbelt import MultipartEncoder
        import io
        
        pdf_content = create_test_pdf()
        
        logger.info("Checking how requests prepares multipart data:")
        
        # Test 1: bytes
        logger.info("\n1. Raw bytes:")
        logger.info(f"   type: {type(pdf_content)}")
        logger.info(f"   has read(): {hasattr(pdf_content, 'read')}")
        
        # Test 2: BytesIO
        bytes_io = io.BytesIO(pdf_content)
        logger.info("\n2. BytesIO:")
        logger.info(f"   type: {type(bytes_io)}")
        logger.info(f"   has read(): {hasattr(bytes_io, 'read')}")
        
        # Test 3: memoryview
        mv = memoryview(pdf_content)
        logger.info("\n3. memoryview:")
        logger.info(f"   type: {type(mv)}")
        logger.info(f"   has read(): {hasattr(mv, 'read')}")
        logger.info(f"   Problem: requests tries to call .read() on it!")
        
        return True
        
    except Exception as e:
        logger.error(f"Inspection failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    logger.info("="*80)
    logger.info("MEMORYVIEW DEBUG SUITE - Testing PDF upload approaches")
    logger.info("="*80)
    
    results = {}
    
    # Check if backend is running
    try:
        logger.info("\nChecking if backend is running...")
        response = requests.get("http://localhost:8000/api/v1/health", timeout=2)
        logger.info(f"✓ Backend is running (status {response.status_code})")
    except Exception as e:
        logger.error(f"✗ Backend not running: {e}")
        logger.error("Please start the backend with: cd backend && uvicorn app.main:app --reload")
        return
    
    # Run inspection first
    inspect_requests_internals()
    
    # Run all tests
    tests = [
        ("Raw bytes in files dict", test_approach_1_raw_bytes),
        ("BytesIO wrapper", test_approach_2_bytesio),
        ("Fake Streamlit UploadedFile", test_approach_3_fake_streamlit),
        ("Fake Streamlit with getvalue", test_approach_4_fake_streamlit_getvalue),
        ("urllib3 direct", test_approach_5_urllib3_directly),
        ("Memoryview (error trigger)", test_approach_6_memoryview_directly),
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = "PASS" if result else "FAIL"
        except Exception as e:
            logger.error(f"Test crashed: {e}")
            results[test_name] = "ERROR"
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("SUMMARY")
    logger.info("="*80)
    
    for test_name, status in results.items():
        symbol = "✓" if status == "PASS" else ("✗" if status == "FAIL" else "⚠")
        logger.info(f"{symbol} {test_name}: {status}")
    
    # Cleanup
    if TEST_PDF_PATH.exists():
        TEST_PDF_PATH.unlink()
        logger.info(f"\nCleaned up {TEST_PDF_PATH}")


if __name__ == "__main__":
    main()
