#!/usr/bin/env python3
"""Quick script to check ChromaDB status."""

import chromadb
from pathlib import Path

# Initialize ChromaDB client
chroma_dir = Path("./data/chroma")
client = chromadb.PersistentClient(path=str(chroma_dir))

# Get collection
try:
    collection = client.get_collection(name="documents")
    count = collection.count()
    print(f"✓ ChromaDB collection found: 'documents'")
    print(f"  - Total embeddings: {count}")
    
    if count > 0:
        # Get a sample to see structure
        results = collection.get(limit=3, include=["documents", "metadatas"])
        print(f"\n✓ Sample embeddings:")
        for i, (doc, meta) in enumerate(zip(results["documents"][:3], results["metadatas"][:3]), 1):
            print(f"  {i}. Page {meta.get('page_number', 'N/A')}: {doc[:60]}...")
    else:
        print("  - No embeddings found (collection is empty)")
except Exception as e:
    print(f"✗ Error: {e}")
    print(f"  Collection may not exist yet")
