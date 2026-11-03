"""
Chat With Documents – Enterprise SaaS Dashboard (Fixed Layout)

Clean, professional Streamlit UI with fixed layout, alignment, and spacing.
"""

import os
import sys
from pathlib import Path
import pandas as pd
import streamlit as st

# Add backend to Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.config import settings

# Page config
st.set_page_config(
    page_title="Chat With Documents - Enterprise",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# MODERN ENTERPRISE DESIGN SYSTEM (2026)
# ============================================================================
def load_enterprise_css():
    """Load modern enterprise SaaS design system with clean typography and layout."""
    css = """
    <style>
    :root {
        --color-primary: #4F46E5;
        --color-primary-dark: #4338CA;
        --color-primary-light: #EEF2FF;
        --color-slate-900: #0F172A;
        --color-slate-800: #1E293B;
        --color-slate-600: #475569;
        --color-slate-400: #94A3B8;
        --color-slate-200: #E2E8F0;
        --color-slate-100: #F1F5F9;
        --color-slate-50: #F8FAFC;
        --color-success: #10B981;
        --color-warning: #F59E0B;
        --color-error: #EF4444;
        --color-info: #3B82F6;
    }

    * { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", sans-serif; }
    html, body { background: var(--color-slate-50); margin: 0; padding: 0; }
    
    [data-testid="stAppViewContainer"] { background: var(--color-slate-50); }
    [data-testid="stMain"] { padding: 1.5rem 2rem !important; }

    /* Hide Streamlit's default page navigation and header clutter */
    [data-testid="stPageContainer"] { max-width: 100% !important; }
    .stApp > header { display: none !important; }

    /* Clean typography with reduced contrast */
    .page-header { margin-bottom: 1.5rem; padding-bottom: 0; }
    .page-title { font-size: 1.875rem; font-weight: 600; color: var(--color-slate-900); margin: 0; letter-spacing: -0.01em; line-height: 1.3; }

    /* Cleaner card styling without harsh borders */
    .card { background: #FFFFFF; border: none; border-radius: 0.75rem; padding: 1.5rem; box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05); transition: box-shadow 0.2s ease; }
    .card:hover { box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08); }
    .card-header { font-size: 1rem; font-weight: 600; color: var(--color-slate-900); margin-bottom: 1.5rem; letter-spacing: -0.01em; }

    /* Modern input styling with soft focus state */
    .stTextArea { margin: 0 !important; padding: 0 !important; }
    .stTextArea textarea { 
        font-size: 0.9rem; 
        border: 1px solid var(--color-slate-200); 
        border-radius: 0.5rem; 
        padding: 0.625rem; 
        color: var(--color-slate-900); 
        background: #FFFFFF; 
        width: 100% !important; 
        box-sizing: border-box; 
        font-weight: 400;
    }
    .stTextArea textarea::placeholder { color: var(--color-slate-400); font-weight: 400; }
    .stTextArea textarea:focus { 
        border-color: var(--color-primary); 
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.08), inset 0 0 0 1px var(--color-primary); 
        outline: none; 
    }

    /* Integrated button action style */
    .stButton { margin: 0.5rem 0 0 0 !important; }
    .stButton > button { 
        font-size: 0.85rem; 
        font-weight: 600; 
        padding: 0.5rem 1rem !important; 
        border-radius: 0.5rem; 
        border: none; 
        cursor: pointer; 
        transition: all 0.15s ease; 
        width: 100% !important; 
        height: auto; 
        letter-spacing: -0.01em;
    }
    .stButton > button[kind="primary"] { 
        background: var(--color-primary) !important; 
        color: #FFFFFF !important; 
        box-shadow: 0 2px 4px rgba(79, 70, 229, 0.15) !important;
    }
    .stButton > button[kind="primary"]:hover { 
        background: var(--color-primary-dark) !important; 
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25) !important; 
        transform: translateY(-1px);
    }
    .stButton > button[kind="primary"]:active { transform: translateY(0); }

    /* Clean compact notifications */
    .stSuccess, .stWarning, .stError, .stInfo {
        margin: 0.5rem 0 !important;
        padding: 0.75rem 1rem !important;
        border-radius: 0.5rem !important;
        border: none !important;
    }

    .stSuccess { background: #F0FDF4; color: #065F46; }
    .stWarning { background: #FFFBEB; color: #92400E; }
    .stError { background: #FEF2F2; color: #7F1D1D; }
    .stInfo { background: #F0F9FF; color: #0C2D6B; }

    /* Modern metric cards */
    .stMetric { 
        background: #FFFFFF; 
        border: 1px solid var(--color-slate-100); 
        padding: 1rem; 
        border-radius: 0.5rem; 
        text-align: center; 
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
    }
    .stMetric label { 
        font-size: 0.7rem; 
        color: var(--color-slate-500); 
        font-weight: 600; 
        text-transform: uppercase; 
        letter-spacing: 0.05em; 
    }
    .stMetric [data-testid="metric-value"] { 
        font-size: 1.75rem; 
        font-weight: 600; 
        color: var(--color-primary); 
        margin-top: 0.5rem; 
    }

    /* Refined typography */
    h1 { font-size: 1.875rem; font-weight: 600; color: var(--color-slate-900); margin: 0 0 0.5rem 0; letter-spacing: -0.01em; }
    h2 { font-size: 1.25rem; font-weight: 600; color: var(--color-slate-900); margin: 1rem 0 0.5rem 0; letter-spacing: -0.01em; }
    h3 { font-size: 1rem; font-weight: 600; color: var(--color-slate-800); margin: 0.75rem 0 0.5rem 0; }
    h4 { font-size: 0.95rem; font-weight: 600; color: var(--color-slate-800); margin: 0.5rem 0 0.375rem 0; }

    body, p { color: var(--color-slate-700); line-height: 1.6; font-weight: 400; }
    a { color: var(--color-primary); text-decoration: none; font-weight: 500; }
    a:hover { text-decoration: underline; color: var(--color-primary-dark); }

    .stExpander { border: 1px solid var(--color-slate-100); border-radius: 0.5rem; background: #FFFFFF; }
    .stExpander [data-testid="stExpanderDetails"] { background: var(--color-slate-50); }
    
    /* Clean spacing */
    .stDivider { background-color: var(--color-slate-100); height: 1px; margin: 1.25rem 0 !important; }
    [data-testid="column"] { gap: 1rem; }

    /* Modern answer box without heavy border */
    .answer-box { 
        background: #FFFFFF; 
        padding: 1.5rem; 
        border-radius: 0.625rem; 
        border-left: 3px solid var(--color-primary);
        font-size: 1rem; 
        line-height: 1.7; 
        color: var(--color-slate-900); 
        margin: 1rem 0; 
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
    }

    /* Modern sidebar navigation */
    .nav-section-title { 
        font-size: 0.7rem; 
        font-weight: 700; 
        color: var(--color-slate-500); 
        text-transform: uppercase; 
        letter-spacing: 0.08em; 
        padding: 0.75rem 1rem 0.5rem 1rem; 
        margin: 0.75rem 0 0.5rem 0; 
    }
    .nav-item { 
        padding: 0.625rem 1rem; 
        margin: 0.25rem 0; 
        border-radius: 0.5rem; 
        cursor: pointer; 
        transition: all 0.15s ease; 
        color: var(--color-slate-700); 
        font-weight: 500;
        font-size: 0.95rem;
        position: relative;
        padding-left: 1rem;
    }
    .nav-item:hover { background: var(--color-slate-50); color: var(--color-primary); }
    .nav-item-active { 
        background: transparent;
        color: var(--color-primary); 
        font-weight: 600;
    }
    .nav-item-active::before { 
        content: ''; 
        position: absolute; 
        left: 0; 
        top: 50%; 
        transform: translateY(-50%); 
        width: 3px; 
        height: 1.5rem; 
        background: var(--color-primary); 
        border-radius: 0 2px 2px 0;
    }

    [data-testid="stSidebar"] { 
        background: #FFFFFF; 
        border-right: 1px solid var(--color-slate-100);
    }

    @media (max-width: 768px) { 
        [data-testid="stMain"] { padding: 1rem 1.25rem !important; }
        .page-title { font-size: 1.5rem; }
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

load_enterprise_css()

# Import API client
from api_client import APIClient

@st.cache_resource
def get_api_client():
    host = settings.api_host if settings.api_host != "0.0.0.0" else "localhost"
    api_url = os.getenv("API_URL", f"http://{host}:{settings.api_port}")
    return APIClient(api_url)

api_client = get_api_client()

# ============================================================================
# SIDEBAR NAVIGATION (Clean and unified)
# ============================================================================
with st.sidebar:
    if "current_page" not in st.session_state:
        st.session_state.current_page = "chat"
    
    st.markdown('<div class="nav-section-title">📊 Main</div>', unsafe_allow_html=True)
    
    if st.button("💬 Chat & Ask", width="stretch", key="nav_chat"):
        st.session_state.current_page = "chat"
        st.rerun()
    
    if st.button("📤 Upload", width="stretch", key="nav_upload"):
        st.session_state.current_page = "upload"
        st.rerun()
    
    if st.button("📋 Library", width="stretch", key="nav_docs"):
        st.session_state.current_page = "documents"
        st.rerun()
    
    st.divider()
    st.markdown('<div class="nav-section-title">⚙️ Tools</div>', unsafe_allow_html=True)
    
    if st.button("🔧 Settings", width="stretch", key="nav_settings"):
        st.session_state.current_page = "settings"
        st.rerun()

# ============================================================================
# PAGE HEADER (Simplified)
# ============================================================================
st.markdown(
    """
    <div class="page-header">
        <h1 class="page-title">Ask Your Documents</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================================
# PAGES WITH FIXED LAYOUT AND ALIGNMENT
# ============================================================================

if st.session_state.current_page == "chat":
    st.divider()
    
    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history first
    if st.session_state.chat_history:
        st.markdown("**Recent Answers**")
        for i, item in enumerate(st.session_state.chat_history[:3]):
            with st.expander(f"Q: {item.get('query', '')[:55]}...", expanded=i == 0):
                st.markdown(f'<div class="answer-box">{item.get("answer", "")}</div>', unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    st.caption(f"📊 {len(item.get('sources', []))} sources used")
                with col2:
                    st.caption(f"⏱️ {pd.Timestamp.now().strftime('%H:%M:%S')}")
        st.divider()
    else:
        st.markdown("**Get Started**")
        st.caption("Ask questions about your uploaded documents. Answers are grounded in document content with source citations.")
        st.divider()
    
    # Modern conversational input at bottom
    st.markdown("**Enter Your Question**")
    
    query = st.text_area(
        "label",
        placeholder="Ask anything about your documents...",
        height=60,
        key="chat_query",
        label_visibility="collapsed"
    )
    
    col_btn, col_spacer = st.columns([1, 4], gap="small")
    
    with col_btn:
        ask_button = st.button(
            "Send",
            width="stretch",
            type="primary",
            key="ask_btn"
        )
    
    # Process question
    if ask_button:
        if not query or not query.strip():
            st.toast("Please enter a question", icon="⚠️")
        else:
            with st.spinner("Analyzing documents..."):
                try:
                    response = api_client.ask_question(query)
                    st.session_state.chat_history.insert(0, response)
                    st.divider()
                    
                    st.markdown("**Answer**")
                    st.markdown(
                        f'<div class="answer-box">{response["answer"]}</div>',
                        unsafe_allow_html=True,
                    )
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if response.get("context_sufficient"):
                            st.success("✓ High Confidence", icon="✅")
                        else:
                            st.warning("⚠ Limited Context", icon="⚠️")
                    with col2:
                        sources_count = len(response.get('sources', []))
                        st.info(f"📊 {sources_count} Sources")
                    with col3:
                        st.caption(f"Generated: {pd.Timestamp.now().strftime('%H:%M:%S')}")
                    
                    if response.get("sources"):
                        st.markdown("**Source Documents**")
                        for i, source in enumerate(response["sources"], 1):
                            with st.expander(
                                f"Document {i}: {source.get('filename', 'Unknown')} - Page {source.get('page_number')}"
                            ):
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.write(source.get("text_preview", "")[:400])
                                with col2:
                                    st.metric("Match", f"{source.get('similarity_score', 0):.0%}")
                    
                    st.rerun()
                
                except Exception as e:
                    st.toast(f"Error: {str(e)}", icon="❌")

elif st.session_state.current_page == "upload":
    st.markdown("### Upload Documents")
    st.caption("Add PDF files to your knowledge base")
    st.divider()
    
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf", help="Max 10MB, max 100 pages")
    
    if uploaded_file is not None:
        st.divider()
        file_size_mb = uploaded_file.size / 1024 / 1024
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Filename", uploaded_file.name[:18] + "..." if len(uploaded_file.name) > 18 else uploaded_file.name)
        with col2:
            st.metric("File Size", f"{file_size_mb:.2f} MB")
        with col3:
            st.metric("Status", "✓ Ready")
        with col4:
            st.metric("Format", "PDF")
        
        st.divider()
        col1, col2 = st.columns([5, 1])
        with col2:
            upload_button = st.button("Upload", width="stretch", type="primary")
        
        if upload_button:
            with st.spinner("Processing PDF..."):
                try:
                    response = api_client.upload_document(uploaded_file)
                    st.success(f"✅ Document uploaded successfully!")
                    st.divider()
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Document ID", response.get("document_id", "")[:8])
                    with col2:
                        st.metric("Chunks", response.get("chunk_count", "?"))
                    with col3:
                        st.metric("Status", response.get("status", "?").title())
                    
                    st.info("✨ Document indexed! Go to Chat to ask questions.")
                except Exception as e:
                    st.toast(f"Upload failed: {str(e)}", icon="❌")
    else:
        st.markdown(
            """
            <div class="card" style="margin-top: 1.5rem;">
                <div class="card-header">Guidelines</div>
                
                **Supported Format**
                - PDF documents only
                
                **File Limits**
                - Maximum: 10 MB
                - Maximum pages: 100
                
                **Processing**
                - Automatic text extraction
                - Smart page chunking
                - Semantic indexing
                - Instant searchability
            </div>
            """,
            unsafe_allow_html=True,
        )

elif st.session_state.current_page == "documents":
    st.markdown("### Your Library")
    st.caption("Manage all indexed documents")
    
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("🔄 Refresh", width="stretch"):
            st.rerun()
    
    st.divider()
    
    with st.spinner("Loading documents..."):
        try:
            doc_list = api_client.list_documents()
            
            if doc_list.get("count", 0) > 0:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Chunks", doc_list.get("count", 0))
                with col2:
                    st.metric("Documents", len(doc_list.get("documents", [])))
                
                st.divider()
                
                if doc_list.get("documents"):
                    for doc in doc_list["documents"]:
                        col1, col2, col3, col4, col5 = st.columns([2.5, 1, 1, 1, 0.5])
                        with col1:
                            st.write(f"**{doc.get('filename', 'Unknown')}**")
                        with col2:
                            st.metric("Chunks", doc.get('chunk_count', 0))
                        with col3:
                            st.metric("Pages", doc.get('page_count', 0))
                        with col4:
                            st.metric("Size", f"{doc.get('size_mb', 0):.1f}MB" if doc.get('size_mb') else "N/A")
                        with col5:
                            if st.button("🗑️", key=f"del_{doc.get('id')}", help="Delete"):
                                with st.spinner("Deleting..."):
                                    try:
                                        api_client.delete_document(doc.get('id'))
                                        st.toast("Deleted", icon="✅")
                                        st.rerun()
                                    except Exception as e:
                                        st.toast(str(e), icon="❌")
                        st.divider()
            else:
                st.info("No documents yet. Go to Upload to add documents.")
        except Exception as e:
            st.toast(f"Error: {str(e)}", icon="❌")

elif st.session_state.current_page == "settings":
    st.markdown("### System Settings")
    st.caption("Configuration and diagnostics")
    st.divider()
    
    st.markdown("**Health Status**")
    try:
        health = api_client.check_health()
        col1, col2, col3 = st.columns(3)
        with col1:
            status_icon = "🟢" if health.get("status") == "healthy" else "🟡"
            st.metric("API Status", f"{status_icon} {health.get('status', 'unknown').title()}")
        with col2:
            st.metric("Version", health.get("version", "?"))
        with col3:
            st.metric("Check Time", health.get("timestamp", "?")[:10])
    except Exception as e:
        st.toast(f"Could not connect: {str(e)}", icon="❌")
    
    st.divider()
    st.markdown("**Configuration**")
    
    col1, col2 = st.columns(2)
    with col1:
        display_host = settings.api_host if settings.api_host != "0.0.0.0" else "localhost"
        st.write(f"**API:** `http://{display_host}:{settings.api_port}`")
        st.write(f"**Max File:** `{settings.max_upload_size / 1024 / 1024:.0f} MB`")
        st.write(f"**Max Pages:** `{settings.max_pdf_pages}`")
    with col2:
        st.write(f"**LLM:** `{settings.llm_provider}`")
        st.write(f"**Model:** `{settings.ollama_model}`")
        st.write(f"**Environment:** `{settings.environment}`")
    
    st.divider()
    st.markdown("**About**")
    st.markdown(
        """
        **Chat With Documents** is an enterprise RAG system for intelligent document analysis.
        
        **Features:** PDF ingestion • Semantic search • AI-powered Q&A • Source citations • Privacy-first
        
        **Technology:** FastAPI • Streamlit • ChromaDB • Ollama | **Version:** 0.1.0
        """
    )

# ============================================================================
# FOOTER WITH PROPER SPACING
# ============================================================================
# Footer links removed for cleaner interface
