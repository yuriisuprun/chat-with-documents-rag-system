"""
Final comprehensive test to identify the EXACT memoryview issue.

KEY INSIGHT from earlier tests:
- BytesIO.getbuffer() returns memoryview
- Streamlit UploadedFile extends BytesIO
- So if something calls .getbuffer() instead of .getvalue(), we get memoryview
- Then requests tries to read the memoryview and fails

Let's test all potential calling patterns:
"""

import io
import logging
import sys

logging.basicConfig(level=logging.DEBUG, format='%(message)s')
logger = logging.getLogger(__name__)

print("=" * 80)
print("TEST: Identifying where memoryview error comes from")
print("=" * 80)

# Check what Streamlit UploadedFile really is
print("\n1. Streamlit UploadedFile inheritance:")
from streamlit.runtime.uploaded_file_manager import UploadedFile as StreamlitUploadedFile
print(f"   Base classes: {StreamlitUploadedFile.__bases__}")
print(f"   -> It's a BytesIO subclass!")

# Create a mock BytesIO that matches Streamlit behavior
class MockUploadedFile(io.BytesIO):
    """Simulates Streamlit's UploadedFile"""
    def __init__(self, content: bytes, name: str):
        super().__init__(content)
        self.name = name

test_content = b"test pdf content"
mock_file = MockUploadedFile(test_content, "test.pdf")

print("\n2. What methods/properties does it have?")
print(f"   .read() -> {type(mock_file.read())}")
mock_file.seek(0)
print(f"   .getvalue() -> {type(mock_file.getvalue())}")
print(f"   .getbuffer() -> {type(mock_file.getbuffer())}")

print("\n3. MEMORYVIEW CHECK:")
buf = mock_file.getbuffer()
print(f"   .getbuffer() returns memoryview: {isinstance(buf, memoryview)}")
print(f"   memoryview has .read(): {hasattr(buf, 'read')}")

print("\n4. What happens in requests.post(files=...)?")
print("   Let's trace different code paths:\n")

import requests
from unittest.mock import patch

# Trace what requests actually does
original_prepare_request = requests.Session.prepare_request

call_sequence = []

def traced_prepare_request(self, req):
    call_sequence.append(("prepare_request", req.files if hasattr(req, 'files') else None))
    return original_prepare_request(self, req)

requests.Session.prepare_request = traced_prepare_request

# Test Case 1: Pass BytesIO directly
print("   Case 1: files={'file': (name, BytesIO_object, type)}")
call_sequence.clear()
try:
    file_obj = io.BytesIO(test_content)
    response = requests.post(
        "http://localhost:8000/api/v1/documents/upload",
        files={'file': ('test.pdf', file_obj, 'application/pdf')},
        timeout=3
    )
    print(f"     Result: {response.status_code}")
except Exception as e:
    print(f"     Error: {type(e).__name__}: {str(e)[:100]}")

# Test Case 2: Pass memoryview directly (should fail)
print("\n   Case 2: files={'file': (name, memoryview_object, type)}")
call_sequence.clear()
try:
    file_obj = memoryview(test_content)
    response = requests.post(
        "http://localhost:8000/api/v1/documents/upload",
        files={'file': ('test.pdf', file_obj, 'application/pdf')},
        timeout=3
    )
    print(f"     Result: {response.status_code}")
except AttributeError as e:
    if 'read' in str(e) or 'memoryview' in str(e):
        print(f"     ERROR (as expected!): {e}")
    else:
        raise
except Exception as e:
    print(f"     Other error: {type(e).__name__}: {str(e)[:100]}")

# Test Case 3: Pass MockUploadedFile (Streamlit-like)
print("\n   Case 3: files={'file': (name, MockUploadedFile_object, type)}")
call_sequence.clear()
try:
    file_obj = MockUploadedFile(test_content, "test.pdf")
    response = requests.post(
        "http://localhost:8000/api/v1/documents/upload",
        files={'file': ('test.pdf', file_obj, 'application/pdf')},
        timeout=3
    )
    print(f"     Result: {response.status_code}")
except Exception as e:
    print(f"     Error: {type(e).__name__}: {str(e)[:100]}")

# Test Case 4: What api_client currently does  
print("\n   Case 4: api_client pattern (read, check type, convert if needed)")
call_sequence.clear()
try:
    file_obj = MockUploadedFile(test_content, "test.pdf")
    
    # This is what api_client does
    if hasattr(file_obj, 'getvalue'):
        content = file_obj.getvalue()
    elif hasattr(file_obj, 'read'):
        file_obj.seek(0)
        content = file_obj.read()
    else:
        content = file_obj
    
    # Ensure bytes, not memoryview
    if isinstance(content, memoryview):
        content = bytes(content)
    elif not isinstance(content, bytes):
        content = bytes(content)
    
    response = requests.post(
        "http://localhost:8000/api/v1/documents/upload",
        files={'file': ('test.pdf', content, 'application/pdf')},
        timeout=3
    )
    print(f"     Result: {response.status_code}")
except Exception as e:
    print(f"     Error: {type(e).__name__}: {str(e)[:100]}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)
print("""
The memoryview error occurs when:
1. You pass a memoryview object directly to requests.post(files=...)
2. requests tries to call .read() on it (looking for file-like object)
3. memoryview doesn't have .read(), so AttributeError: "memoryview has no attribute read"

The fix in api_client is CORRECT:
- Check if result from .getvalue() is memoryview
- If yes, convert to bytes: bytes(memoryview_obj)
- Pass bytes to requests.post(files=...)

The issue might be that:
- The current code path isn't being executed (maybe a different code path in Streamlit)
- Or there's a Streamlit interceptor modifying the request

ACTION: Check if the fix is actually being applied in production!
""")
