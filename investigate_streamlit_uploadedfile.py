"""
Investigate what Streamlit UploadedFile actually is and how it behaves.

Key finding from initial tests:
- Our current api_client.py tries to call .read() on the file object  
- Then passes the bytes to requests.post(files=...)
- But the error says "memoryview has no attribute read"

This suggests that somewhere in the chain, something is being converted to memoryview
BEFORE we pass it to requests, or Streamlit is doing something weird with .getvalue()
"""

import io
import sys

print("=" * 80)
print("STREAMLIT UPLOADEDFILE INVESTIGATION")
print("=" * 80)

# Try to import Streamlit
try:
    import streamlit as st
    from streamlit.runtime.uploaded_file_manager import UploadedFile
    print(f"\nStreamlit version: {st.__version__}")
    
    # Check UploadedFile class
    print(f"\nStreamlit UploadedFile:")
    print(f"  Class: {UploadedFile}")
    print(f"  MRO: {UploadedFile.__mro__}")
    
    # Create a test instance
    test_data = b"Hello, World!"
    uploaded_file = UploadedFile(
        name="test.txt",
        data=io.BytesIO(test_data),
        type="text/plain"
    )
    
    print(f"\nStreamlit UploadedFile instance:")
    print(f"  Type: {type(uploaded_file)}")
    print(f"  Name: {uploaded_file.name}")
    
    # Check methods
    print(f"\nMethods:")
    print(f"  .read(): {callable(getattr(uploaded_file, 'read', None))}")
    print(f"  .seek(): {callable(getattr(uploaded_file, 'seek', None))}")
    print(f"  .getvalue(): {callable(getattr(uploaded_file, 'getvalue', None))}")
    print(f"  .getbuffer(): {callable(getattr(uploaded_file, 'getbuffer', None))}")
    
    # Test each method
    print(f"\nTesting methods:")
    
    # Reset before testing
    uploaded_file.seek(0)
    
    # Test read()
    print(f"  .read() returns: {type(uploaded_file.read())}")
    uploaded_file.seek(0)
    
    # Test getvalue()
    result_getvalue = uploaded_file.getvalue()
    print(f"  .getvalue() returns: {type(result_getvalue)}")
    
    # Test getbuffer()
    try:
        result_getbuffer = uploaded_file.getbuffer()
        print(f"  .getbuffer() returns: {type(result_getbuffer)}")
        if isinstance(result_getbuffer, memoryview):
            print(f"    ^ This is a memoryview!")
            print(f"    Does memoryview have .read()? {hasattr(result_getbuffer, 'read')}")
    except Exception as e:
        print(f"  .getbuffer() raised: {e}")
    
    # Simulate what our api_client does
    print(f"\nSimulating api_client.upload_document():")
    print(f"  1. Check if file has .getvalue(): {hasattr(uploaded_file, 'getvalue')}")
    if hasattr(uploaded_file, 'getvalue'):
        print(f"  2. Call .getvalue()")
        content = uploaded_file.getvalue()
        print(f"     -> Returns: {type(content)}")
        print(f"     -> Length: {len(content)}")
        
        # This is what api_client currently does
        if isinstance(content, memoryview):
            print(f"  3. Content is memoryview, would convert to bytes")
            content = bytes(content)
        elif not isinstance(content, bytes):
            print(f"  3. Content is {type(content)}, would convert to bytes")
            content = bytes(content)
        else:
            print(f"  3. Content already bytes")
        
        print(f"     -> Final type: {type(content)}")
    
except ImportError:
    print("Streamlit not installed, simulating behavior...")
    print("\nSimulating Streamlit's UploadedFile as a BytesIO subclass:")
    
    class FakeUploadedFile(io.BytesIO):
        """Fake version mimicking Streamlit's UploadedFile"""
        
        def __init__(self, name, data, type):
            if isinstance(data, io.BytesIO):
                super().__init__(data.getvalue())
            else:
                super().__init__(data)
            self.name = name
            self.type = type
    
    test_data = b"Hello, World!"
    uploaded_file = FakeUploadedFile("test.txt", io.BytesIO(test_data), "text/plain")
    
    print(f"  Type: {type(uploaded_file)}")
    print(f"  .getvalue() type: {type(uploaded_file.getvalue())}")
    print(f"  .getbuffer() type: {type(uploaded_file.getbuffer())}")
    
    # Check if getbuffer() returns memoryview
    buf = uploaded_file.getbuffer()
    print(f"  .getbuffer() is memoryview: {isinstance(buf, memoryview)}")
    if isinstance(buf, memoryview):
        print(f"  memoryview.read() exists: {hasattr(buf, 'read')}")


# Now let's check what happens when requests processes these
print("\n" + "=" * 80)
print("HOW REQUESTS HANDLES DIFFERENT FILE TYPES")
print("=" * 80)

from requests import Request

test_data = b"Test PDF content"

cases = [
    ("bytes", test_data),
    ("BytesIO", io.BytesIO(test_data)),
    ("memoryview", memoryview(test_data)),
]

if 'UploadedFile' in locals():
    # Also test real Streamlit if available
    cases.append(("Streamlit UploadedFile", UploadedFile(
        name="test.pdf",
        data=io.BytesIO(test_data),
        type="application/pdf"
    )))

for case_name, file_obj in cases:
    print(f"\nCase: {case_name}")
    print(f"  Input type: {type(file_obj)}")
    
    try:
        req = Request(
            'POST',
            'http://localhost:8000/api/v1/test',
            files={'file': ('test.pdf', file_obj, 'application/pdf')}
        )
        prepared = req.prepare()
        
        print(f"  Prepared body type: {type(prepared.body)}")
        print(f"  Prepared body length: {len(prepared.body) if hasattr(prepared.body, '__len__') else 'N/A'}")
        
    except Exception as e:
        print(f"  ERROR preparing request: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)
print("""
Based on the investigation:

1. Streamlit's UploadedFile is a BytesIO subclass
2. BytesIO.getbuffer() returns a memoryview object
3. If api_client calls .getvalue() on UploadedFile, it gets bytes (OK)
4. If api_client calls .getbuffer() on UploadedFile, it gets memoryview (PROBLEM!)

The memoryview error "memoryview has no attribute read" would occur if:
- Something in the request preparation pipeline tries to call .read() on a memoryview
- This happens when requests tries to process the file tuple

SOLUTION: Always ensure we pass bytes or BytesIO to requests.post(files=...), 
never memoryview!
""")
