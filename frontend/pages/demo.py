"""
Demo page showing example queries and workflows.
"""

import streamlit as st

st.set_page_config(page_title="Demo", page_icon="🎯")

st.title("🎯 Demo & Examples")

st.markdown(
    """
    This page demonstrates the capabilities of the Chat With Documents system.
    """
)

# Example 1: Document Upload
with st.expander("📤 Example 1: Uploading a Document", expanded=True):
    st.markdown(
        """
        ### Steps to upload a document:
        
        1. Go to the **Upload** tab
        2. Click "Choose a PDF file"
        3. Select your PDF document (max 10MB, 100 pages)
        4. Click "Upload & Index"
        5. Wait for processing to complete
        
        The system will:
        - Extract text from the PDF
        - Split content into chunks
        - Generate embeddings
        - Index in the vector store
        """
    )

# Example 2: Asking Questions
with st.expander("💬 Example 2: Asking Questions", expanded=False):
    st.markdown(
        """
        ### How to ask effective questions:
        
        **Good questions:**
        - "What is the main topic of the document?"
        - "How does the process work?"
        - "List the key benefits"
        - "Summarize the conclusion"
        
        **Tips for better answers:**
        1. Be specific about what you want to know
        2. Use keywords from the document
        3. Ask one question at a time
        4. Provide context if needed
        
        **The system will:**
        - Search for relevant document sections
        - Generate an AI-powered answer
        - Show source references
        - Indicate if context is sufficient
        """
    )

# Example 3: Understanding Sources
with st.expander("📎 Example 3: Understanding Sources", expanded=False):
    st.markdown(
        """
        ### What are source references?
        
        For every answer, the system shows:
        - **Document filename**: Which document contains the information
        - **Page number**: Which page to find the source
        - **Similarity score**: How relevant the chunk is (0-100%)
        - **Text preview**: First 200 characters of the source
        
        ### Why sources matter:
        - Verify answer accuracy
        - Find more information in original document
        - Understand context better
        - Trust the AI system more
        """
    )

# Example 4: Managing Documents
with st.expander("📋 Example 4: Managing Documents", expanded=False):
    st.markdown(
        """
        ### Document management features:
        
        **View documents:**
        1. Go to the **Documents** tab
        2. See total chunks indexed
        3. View individual documents with details
        
        **Delete documents:**
        1. Find the document you want to remove
        2. Click the 🗑️ (trash) button
        3. Confirm the deletion
        
        **Notes:**
        - Deletion removes the document from the vector store
        - This frees up storage and search space
        - The original file is not affected
        """
    )

# Example 5: System Health
with st.expander("⚙️ Example 5: System Health & Settings", expanded=False):
    st.markdown(
        """
        ### Monitoring system health:
        
        In the **Settings** tab, you can see:
        - API connection status
        - LLM (Ollama) status
        - Vector database status
        - System configuration
        
        ### Troubleshooting:
        - If connection fails, check if backend is running
        - If LLM is offline, start Ollama: `ollama serve`
        - Check logs for detailed error information
        """
    )

st.divider()

# Quick start guide
st.subheader("⚡ Quick Start")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        **1. Upload**
        
        📤 Go to Upload tab
        
        Select PDF file
        
        Click Upload
        """
    )

with col2:
    st.markdown(
        """
        **2. Ask**
        
        💬 Go to Chat tab
        
        Type your question
        
        Click Ask
        """
    )

with col3:
    st.markdown(
        """
        **3. Explore**
        
        📎 Review sources
        
        Follow up questions
        
        Discover insights
        """
    )

st.divider()

# FAQ
st.subheader("❓ Frequently Asked Questions")

faq_items = [
    {
        "q": "What file formats are supported?",
        "a": "Currently, only PDF files are supported. Maximum size is 10MB with a limit of 100 pages per document.",
    },
    {
        "q": "How long does indexing take?",
        "a": "It depends on document size: small PDFs (~1MB) take 1-2 seconds, medium (1-5MB) take 5-10 seconds, large (5-10MB) take 15-30 seconds.",
    },
    {
        "q": "Can I use this offline?",
        "a": "Yes! The system uses a local LLM (Ollama) so everything runs on your machine. No external API calls are made.",
    },
    {
        "q": "How accurate are the answers?",
        "a": "Accuracy depends on the quality of source documents and specificity of questions. The system shows source references so you can verify answers.",
    },
    {
        "q": "Can I delete documents?",
        "a": "Yes, use the Documents tab to delete any indexed document. This removes it from the search index but doesn't delete the original file.",
    },
    {
        "q": "What if the LLM is not available?",
        "a": "Make sure Ollama is running. Start it with: `ollama serve` in your terminal. Check Settings tab for connection status.",
    },
]

for item in faq_items:
    with st.expander(f"**Q: {item['q']}**"):
        st.write(item["a"])

st.divider()

# Tips & Tricks
st.subheader("💡 Tips & Tricks")

st.markdown(
    """
    ### For Better Results:
    
    1. **Use specific keywords** - Instead of "tell me about it", ask "what are the main features?"
    2. **Ask follow-ups** - Refine answers with additional questions
    3. **Check sources** - Always verify answers match the source content
    4. **Upload diverse docs** - Mix different documents for richer context
    5. **Use the history** - Previous questions are saved in the chat history
    
    ### System Configuration:
    
    1. **Change LLM model** - Edit Ollama configuration for different models
    2. **Adjust similarity threshold** - Modify settings for more/fewer results
    3. **Monitor resources** - Check system health for performance metrics
    """
)
