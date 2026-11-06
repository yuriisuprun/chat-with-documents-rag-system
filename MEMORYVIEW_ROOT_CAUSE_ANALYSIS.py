"""
ROOT CAUSE ANALYSIS: Finding where "memoryview has no attribute read" comes from

Theory: The error might be in urllib3 or somewhere deep in requests' multipart encoding,
not visible from high-level requests API tests.

Let's trace the ENTIRE request encoding pipeline:
"""

import io
import sys
import traceback
from unittest.mock import patch
import logging

logging.basicConfig(level=logging.DEBUG)

print("=" * 90)
print("ROOT CAUSE: Tracing multipart encoding pipeline for memoryview")
print("=" * 90)

# We need to trace at the urllib3 level where multipart is actually encoded
from urllib3.filepost import encode_multipart_formdata, RequestField

print("\n1. Direct urllib3 test with different types:")

test_content = b"test content"

cases = [
    ("bytes", test_content),
    ("BytesIO", io.BytesIO(test_content)),
    ("memoryview", memoryview(test_content)),
]

for case_name, content in cases:
    print(f"\n   Testing: {case_name}")
    try:
        # This is what urllib3 does internally
        fields = [
            RequestField(
                name='file',
                data=content,
                filename='test.pdf',
                headers={'Content-Type': 'application/pdf'}
            )
        ]
        fields[0].make_multipart()
        
        body, content_type = encode_multipart_formdata(fields)
        print(f"     SUCCESS: Encoded {len(body)} bytes")
        
    except AttributeError as e:
        print(f"     ATTRIBUTEERROR: {e}")
        traceback.print_exc()
    except Exception as e:
        print(f"     ERROR: {type(e).__name__}: {e}")
        traceback.print_exc()


print("\n" + "=" * 90)
print("2. Checking RequestField behavior:")

field_bytes = RequestField(
    name='file',
    data=test_content,
    filename='test.pdf'
)
field_bytesio = RequestField(
    name='file',
    data=io.BytesIO(test_content),
    filename='test.pdf'
)
field_memoryview = RequestField(
    name='file',
    data=memoryview(test_content),
    filename='test.pdf'
)

for field_name, field in [
    ("bytes", field_bytes),
    ("BytesIO", field_bytesio),
    ("memoryview", field_memoryview),
]:
    print(f"\n   {field_name}:")
    print(f"     .data type: {type(field.data)}")
    print(f"     .data has .read(): {hasattr(field.data, 'read')}")
    try:
        field.make_multipart()
        print(f"     make_multipart(): OK")
    except Exception as e:
        print(f"     make_multipart() ERROR: {type(e).__name__}: {e}")


print("\n" + "=" * 90)
print("3. Trace requests' internal request preparation:")

import requests
from requests.models import RequestEncodingMixin

# Monkey-patch to trace
original_encode = RequestEncodingMixin._encode_files

def traced_encode(self, files, data):
    print(f"\n   _encode_files called:")
    if files:
        for key, file_tuple in files.items():
            print(f"     files['{key}'] type: {type(file_tuple)}")
            if isinstance(file_tuple, tuple):
                print(f"       -> tuple with {len(file_tuple)} items:")
                for i, item in enumerate(file_tuple):
                    print(f"          [{i}]: {type(item)} - {repr(item)[:50] if not isinstance(item, (bytes, memoryview)) else f'{type(item).__name__} of len {len(item)}'}")
    
    try:
        result = original_encode(self, files, data)
        print(f"   _encode_files result: Success")
        return result
    except Exception as e:
        print(f"   _encode_files FAILED: {type(e).__name__}: {e}")
        traceback.print_exc()
        raise

RequestEncodingMixin._encode_files = traced_encode

print("\n4. Test with requests.post directly:")

for case_name, content in cases:
    print(f"\n   Case: {case_name}")
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/documents/upload",
            files={'file': ('test.pdf', content, 'application/pdf')},
            timeout=3
        )
        print(f"     Status: {response.status_code}")
    except AttributeError as e:
        if 'read' in str(e) or 'memoryview' in str(e):
            print(f"     FOUND IT! AttributeError: {e}")
        else:
            print(f"     AttributeError (different): {e}")
        traceback.print_exc()
    except Exception as e:
        print(f"     Error: {type(e).__name__}: {str(e)[:100]}")


print("\n" + "=" * 90)
print("FINDINGS SUMMARY:")
print("=" * 90)
print("""
If the AttributeError: 'memoryview' has no attribute 'read' appears ONLY in Streamlit,
but NOT when running direct tests, then:

POSSIBLE CAUSES:
1. Streamlit wraps the file upload in some middleware
2. Streamlit uses a different version of requests or urllib3
3. Streamlit modifies sys.modules or patches requests globally
4. The error occurs in a different code path (maybe streaming, chunking, etc.)

SOLUTIONS TO TRY:
1. Check what version of requests/urllib3 Streamlit is using
2. Add explicit type conversion in api_client BEFORE sending to requests
3. Test with Streamlit's own test utilities
4. Check if there's a Streamlit-specific file upload mechanism we should use

NEXT STEP:
- Check Streamlit's dependencies
- Check if there's a specific Streamlit API for HTTP requests
- Test if the issue is in api_client or in how Streamlit calls it
""")
