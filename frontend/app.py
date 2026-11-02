"""
Chat With Documents – Frontend Application

Streamlit-based UI for the RAG system that allows users to:
- Upload PDF documents
- View indexed documents
- Ask questions and receive AI-powered answers with sources
"""

import os
import sys
from pathlib import Path

import streamlit as st

# Add backend to Python path for importing config
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.config import settings

# Configure Streamlit page
st.set_page_config(
    page_title="Chat With Documents",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load custom CSS
def load_css():
    """Load custom CSS styling."""
    css = """
    <style>
    /* Main container styling */
    .main {
        padding: 2rem;
    }
    
    /* Header styling */
    .header-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    
    .header-subtitle {
        font-size: 1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    
    /* Card styling */
    .info-card {
        background-color: #f0f2f6;
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    
    /* Source reference styling */
    .source-reference {
        background-color: #f9f9f9;
        border-left: 3px solid #28a745;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
        font-size: 0.9rem;
    }
    
    /* Answer styling */
    .answer-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    
    /* Status badge */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.85rem;
        font-weight: bold;
    }
    
    .status-indexed {
        background-color: #28a745;
        color: white;
    }
    
    .status-error {
        background-color: #dc3545;
        color: white;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

load_css()

# Import API client
from api_client import APIClient

# Initialize API client with backend URL
@st.cache_resource
def get_api_client():
    """Get or create API client."""
    # Use 0.0.0.0 for server binding, but localhost for client connections
    host = settings.api_host if settings.api_host != "0.0.0.0" else "localhost"
    api_url = os.getenv("API_URL", f"http://{host}:{settings.api_port}")
    return APIClient(api_url)

api_client = get_api_client()

# Page header
st.markdown(
    '<div class="header-title">📚 Chat With Documents</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="header-subtitle">Ask questions about your PDF documents using AI</div>',
    unsafe_allow_html=True,
)

# Main layout
tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "📤 Upload", "📋 Documents", "⚙️ Settings"])

# ============================================================================
# TAB 1: CHAT
# ============================================================================
with tab1:
    st.header("Ask Questions")
    
    # Chat interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_area(
            "Your Question",
            placeholder="Ask a question about your documents...",
            height=80,
            key="chat_query",
        )
    
    with col2:
        st.write("")
        st.write("")
        ask_button = st.button("Ask", use_container_width=True, type="primary")
    
    # Show recent queries
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if ask_button:
        if not query or not query.strip():
            st.error("Please enter a question")
        else:
            with st.spinner("Searching and generating answer..."):
                try:
                    response = api_client.ask_question(query)
                    
                    # Add to history
                    st.session_state.chat_history.insert(0, response)
                    
                    # Display answer
                    st.subheader("Answer")
                    st.markdown(
                        f'<div class="answer-box">{response["answer"]}</div>',
                        unsafe_allow_html=True,
                    )
                    
                    # Display context sufficiency
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if response["context_sufficient"]:
                            st.success("✅ Context sufficient")
                        else:
                            st.warning("⚠️ Limited context")
                    
                    # Display sources
                    if response["sources"]:
                        st.subheader("Sources")
                        for source in response["sources"]:
                            with st.expander(
                                f"📄 {source['filename']} (Page {source['page_number']})"
                            ):
                                st.write(f"**Document ID:** {source['document_id']}")
                                st.write(f"**Page:** {source['page_number']}")
                                st.write(f"**Similarity:** {source['similarity_score']:.2%}")
                                st.write(f"**Preview:** {source['text_preview']}")
                    else:
                        st.info("No relevant sources found in documents")
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    # Display chat history
    if st.session_state.chat_history:
        st.divider()
        st.subheader("Recent Questions")
        
        for i, item in enumerate(st.session_state.chat_history[:5]):
            with st.expander(f"Q: {item['query'][:60]}..."):
                st.write(f"**Answer:** {item['answer'][:200]}...")
                st.write(f"**Sources:** {len(item['sources'])} found")

# ============================================================================
# TAB 2: UPLOAD
# ============================================================================
with tab2:
    st.header("Upload Documents")
    
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type="pdf",
        help="Maximum file size: 10MB, Maximum pages: 100",
    )
    
    if uploaded_file is not None:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write(f"**File:** {uploaded_file.name}")
            st.write(f"**Size:** {uploaded_file.size / 1024 / 1024:.2f} MB")
        
        with col2:
            st.write("")
            upload_button = st.button(
                "Upload & Index",
                use_container_width=True,
                type="primary",
            )
        
        if upload_button:
            with st.spinner("Uploading and indexing document..."):
                try:
                    response = api_client.upload_document(uploaded_file)
                    
                    st.success(f"✅ {response['message']}")
                    
                    # Display document info
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Document ID", response["document_id"][:8] + "...")
                    with col2:
                        st.metric("Filename", response["filename"])
                    with col3:
                        st.metric("Status", response["status"])
                    
                    # Clear the file uploader
                    st.session_state.uploaded_file = None
                    
                except Exception as e:
                    st.error(f"Error uploading document: {str(e)}")
    
    # Upload information
    st.divider()
    st.info(
        """
        **Upload Requirements:**
        - File type: PDF only
        - Maximum size: 10 MB
        - Maximum pages: 100
        
        The system will automatically:
        1. Extract text from the PDF
        2. Split into chunks
        3. Generate embeddings
        4. Index in vector store
        """
    )

# ============================================================================
# TAB 3: DOCUMENTS
# ============================================================================
with tab3:
    st.header("Indexed Documents")
    
    if st.button("🔄 Refresh", key="refresh_docs"):
        st.session_state.last_refresh = None
    
    with st.spinner("Loading documents..."):
        try:
            doc_list = api_client.list_documents()
            
            if doc_list["count"] > 0:
                st.success(f"✅ {doc_list['count']} chunks indexed")
                
                # Display statistics
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Chunks", doc_list["count"])
                
                # Display documents
                if doc_list["documents"]:
                    st.subheader("Documents")
                    for doc in doc_list["documents"]:
                        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                        
                        with col1:
                            st.write(f"**{doc['filename']}**")
                        
                        with col2:
                            st.write(f"{doc['chunk_count']} chunks")
                        
                        with col3:
                            st.write(f"{doc['page_count']} pages")
                        
                        with col4:
                            if st.button(
                                "🗑️",
                                key=f"delete_{doc['id']}",
                                help="Delete this document",
                            ):
                                with st.spinner("Deleting..."):
                                    try:
                                        api_client.delete_document(doc['id'])
                                        st.success(f"Deleted {doc['filename']}")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
            else:
                st.info("No documents indexed yet. Upload a PDF to get started.")
        
        except Exception as e:
            st.error(f"Error loading documents: {str(e)}")

# ============================================================================
# TAB 4: SETTINGS
# ============================================================================
with tab4:
    st.header("Settings & Information")
    
    # API Configuration
    st.subheader("API Configuration")
    # Use localhost for display instead of 0.0.0.0
    display_host = settings.api_host if settings.api_host != "0.0.0.0" else "localhost"
    api_url = os.getenv("API_URL", f"http://{display_host}:{settings.api_port}")
    st.write(f"**API URL:** {api_url}")
    st.write(f"**API Host:** {display_host}")
    st.write(f"**API Port:** {settings.api_port}")
    
    # System Configuration
    st.subheader("System Configuration")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Max Upload Size:** {settings.max_upload_size / 1024 / 1024:.0f} MB")
        st.write(f"**Max PDF Pages:** {settings.max_pdf_pages}")
        st.write(f"**Embedding Model:** {settings.embedding_model[:40]}...")
    
    with col2:
        st.write(f"**LLM Provider:** {settings.llm_provider}")
        st.write(f"**LLM Model:** {settings.ollama_model}")
        st.write(f"**Environment:** {settings.environment}")
    
    # System Health
    st.subheader("System Health")
    try:
        health = api_client.check_health()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_color = "green" if health["status"] == "healthy" else "orange"
            st.write(f"**Status:** :{status_color}[{health['status'].upper()}]")
        
        with col2:
            st.write(f"**Version:** {health['version']}")
        
        with col3:
            st.write(f"**Timestamp:** {health['timestamp'][:19]}")
        
        # Services status
        st.write("**Services:**")
        for service_name, service_status in health["services"].items():
            status_icon = "✅" if service_status else "❌"
            st.write(f"{status_icon} {service_name}: {service_status}")
    
    except Exception as e:
        st.error(f"Could not connect to API: {str(e)}")
    
    # About
    st.divider()
    st.subheader("About")
    st.write(
        """
        **Chat With Documents** is an AI-powered RAG (Retrieval-Augmented Generation) system
        that allows you to upload PDF documents and ask questions about their contents.
        
        **Features:**
        - 📤 Upload and automatically index PDF documents
        - 🔍 Semantic search over document content
        - 🤖 AI-powered answers using local LLMs
        - 📎 Source citations for every answer
        - 🔒 Privacy-first design (no external API calls)
        
        **Built with:**
        - FastAPI (Backend)
        - Streamlit (Frontend)
        - ChromaDB (Vector Store)
        - Sentence Transformers (Embeddings)
        - Ollama (Local LLM)
        
        **Version:** 0.1.0 (Phase 6)
        """
    )

# Footer
st.divider()
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    st.caption("🏠 [Documentation](https://github.com/yourusername/chat-with-documents)")
with col2:
    st.caption("💬 [Issues](https://github.com/yourusername/chat-with-documents/issues)")
with col3:
    st.caption("⭐ [GitHub](https://github.com/yourusername/chat-with-documents)")
