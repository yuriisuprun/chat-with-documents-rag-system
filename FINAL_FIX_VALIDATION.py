"""
FINAL FIX VALIDATION

Root Cause Found: urllib3 encode_multipart_formdata() CANNOT handle file-like objects directly!
- bytes: WORKS
- BytesIO: FAILS (TypeError: bytes-like object required, not '_io.BytesIO')  
- memoryview: WORKS

But requests.post(files=...) handles this layer. So where does the memoryview error come from?

Answer: If requests.post receives a file-like object that has a .read() that returns memoryview,
and then requests tries to read that memoryview, it will fail at the urllib3 layer!

For example:
- BytesIO.read() returns bytes (OK)
- But if something returns a memoryview from read(), then urllib3 fails

The FIX: Ensure we ALWAYS pass either:
1. Raw bytes
2. A file-like object whose .read() returns bytes (not memoryview)
"""

import io
import requests

print("=" * 90)
print("TESTING: Understanding the memoryview/BytesIO issue")
print("=" * 90)

test_content = b"test pdf"

print("\n1. What urllib3.filepost.encode_multipart_formdata accepts:")

from urllib3.filepost import encode_multipart_formdata, RequestField

cases = [
    ("Raw bytes", test_content),
    ("BytesIO", io.BytesIO(test_content)),
    ("BytesIO (pre-read)", io.BytesIO(test_content).read()),
    ("memoryview", memoryview(test_content)),
]

for name, data in cases:
    try:
        fields = [RequestField(name='file', data=data, filename='test.pdf')]
        fields[0].make_multipart()
        body, ct = encode_multipart_formdata(fields)
        print(f"  {name:30} OK - {len(body)} bytes")
    except Exception as e:
        print(f"  {name:30} FAIL - {type(e).__name__}: {str(e)[:50]}")


print("\n2. What requests.post accepts:")

for name, data in cases:
    try:
        # Fake BytesIO needs to be reset before each request
        if hasattr(data, 'seek'):
            data.seek(0)
        
        response = requests.post(
            "http://localhost:8000/api/v1/documents/upload",
            files={'file': ('test.pdf', data, 'application/pdf')},
            timeout=3
        )
        print(f"  {name:30} OK - Status {response.status_code}")
    except Exception as e:
        err = str(e)[:60]
        print(f"  {name:30} FAIL - {type(e).__name__}: {err}")


print("\n3. CRITICAL: File-like object whose read() returns memoryview")

class BadBytesIO(io.BytesIO):
    """BytesIO that returns memoryview instead of bytes from read()"""
    def read(self, *args):
        data = super().read(*args)
        return memoryview(data)  # Return memoryview instead of bytes!


try:
    bad_file = BadBytesIO(test_content)
    response = requests.post(
        "http://localhost:8000/api/v1/documents/upload",
        files={'file': ('test.pdf', bad_file, 'application/pdf')},
        timeout=3
    )
    print(f"  BadBytesIO - Status {response.status_code}")
except AttributeError as e:
    print(f"  BadBytesIO - ATTRIBUTEERROR: {e}")
    if 'read' in str(e) and 'memoryview' in str(e):
        print(f"    ^^^ THIS IS THE ERROR WE'RE LOOKING FOR!")
except Exception as e:
    print(f"  BadBytesIO - {type(e).__name__}: {e}")


print("\n4. THE ACTUAL STREAMLIT UPLOADEDFILE TEST:")

try:
    from streamlit.runtime.uploaded_file_manager import UploadedFile as RealUploadedFile
    
    # We can't easily instantiate real UploadedFile, but we can check
    print(f"  RealUploadedFile bases: {RealUploadedFile.__bases__}")
    
    # Simulate: does Streamlit UploadedFile override read()?
    import inspect
    if hasattr(RealUploadedFile, 'read'):
        # Check if it's inherited or overridden
        method = getattr(RealUploadedFile, 'read')
        owner = method.__self__.__class__ if hasattr(method, '__self__') else None
        print(f"  read() method defined in: {owner or 'BytesIO (inherited)'}")
    
    # The key question: does UploadedFile.read() return bytes or memoryview?
    # Based on BytesIO inheritance, it should return bytes
    # So the memoryview error must come from somewhere else
    
except Exception as e:
    print(f"  Could not test real UploadedFile: {e}")


print("\n" + "=" * 90)
print("CONCLUSION & FIX")
print("=" * 90)
print("""
The "memoryview has no attribute read" error happens when:

1. A file-like object's .read() method returns memoryview instead of bytes
2. requests tries to encode this for multipart/form-data
3. urllib3 gets a memoryview and tries to call .read() on it (looking for more file-like objects)
4. memoryview doesn't have .read(), so AttributeError

For Streamlit UploadedFile (which inherits from BytesIO):
- .read() should return bytes (OK)
- .getvalue() returns bytes (OK)
- .getbuffer() returns memoryview (but we don't use this)

The FIX already in api_client.py is CORRECT:
1. Use .getvalue() to get all content at once (no chunked reading)
2. Check if result is memoryview and convert to bytes
3. Pass bytes to requests.post()

However, if we're STILL seeing the error, it might be:
- The api_client code path isn't being executed
- There's a Streamlit middleware intercepting
- The error message is coming from a cached traceback

RECOMMENDATION:
- Add explicit logging to api_client to confirm code path execution
- Add a safety check: always ensure content is bytes before requests.post()
- Test directly with Streamlit in a mini app
""")
