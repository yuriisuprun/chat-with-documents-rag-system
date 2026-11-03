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
# ENTERPRISE DESIGN SYSTEM WITH LAYOUT FIXES
# ============================================================================
def load_enterprise_css():
    """Load enterprise SaaS design system with layout and alignment fixes."""
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
        --color-slate-50: #F8FAFC;
        --color-success: #10B981;
        --color-warning: #F59E0B;
        --color-error: #EF4444;
        --color-info: #3B82F6;
    }

    * { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    html, body { background: var(--color-slate-50); margin: 0; padding: 0; }
    
    [data-testid="stAppViewContainer"] { background: var(--color-slate-50); }
    [data-testid="stMain"] { padding: 2rem 3rem !important; }

    /* FIX: Hide Streamlit's default page navigation and header clutter */
    [data-testid="stPageContainer"] { max-width: 100% !important; }
    .stApp > header { display: none !important; }

    .page-header { margin-bottom: 2.5rem; padding-bottom: 0; }
    .page-title { font-size: 2.5rem; font-weight: 800; color: var(--color-slate-900); margin: 0 0 0.5rem 0; letter-spacing: -0.02em; }
    .page-subtitle { font-size: 1rem; color: var(--color-slate-600); margin: 0; font-weight: 400; }

    .card { background: #FFFFFF; border: 1px solid var(--color-slate-200); border-radius: 0.75rem; padding: 1.5rem; box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08); transition: all 0.2s; }
    .card:hover { box-shadow: 0 4px 12px rgba(15, 23, 42, 0.12); border-color: var(--color-slate-300); }
    .card-header { font-size: 1.1rem; font-weight: 700; color: var(--color-slate-900); margin-bottom: 1.5rem; }

    /* FIX: Input & button alignment */
    .stTextArea { margin: 0 !important; padding: 0 !important; }
    .stTextArea textarea { font-size: 1rem; border: 1.5px solid var(--color-slate-200); border-radius: 0.625rem; padding: 0.875rem; color: var(--color-slate-900); background: #FFFFFF; width: 100% !important; box-sizing: border-box; }
    .stTextArea textarea::placeholder { color: var(--color-slate-400); }
    .stTextArea textarea:focus { border-color: var(--color-primary); box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1); outline: none; }

    .stButton { margin: 0 !important; }
    .stButton > button { font-size: 0.95rem; font-weight: 600; padding: 0.75rem 1.5rem !important; border-radius: 0.625rem; border: none; cursor: pointer; transition: all 0.2s; box-shadow: 0 2px 4px rgba(15, 23, 42, 0.08); width: 100% !important; height: auto; }
    .stButton > button[kind="primary"] { background: var(--color-primary) !important; color: #FFFFFF !important; }
    .stButton > button[kind="primary"]:hover { background: var(--color-primary-dark) !important; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3) !important; transform: translateY(-1px); }
    .stButton > button[kind="primary"]:active { transform: translateY(0); }

    /* FIX: Compact notifications */
    .stSuccess, .stWarning, .stError, .stInfo {
        margin: 0.5rem 0 !important;
        padding: 0.75rem 1rem !important;
        border-radius: 0.5rem !important;
    }

    .stSuccess { background: #F0FDF4; border-left: 3px solid var(--color-success) !important; border-right: 1px solid var(--color-slate-200); border-top: 1px solid var(--color-slate-200); border-bottom: 1px solid var(--color-slate-200); }
    .stWarning { background: #FFFBEB; border-left: 3px solid var(--color-warning) !important; border-right: 1px solid var(--color-slate-200); border-top: 1px solid var(--color-slate-200); border-bottom: 1px solid var(--color-slate-200); }
    .stError { background: #FEF2F2; border-left: 3px solid var(--color-error) !important; border-right: 1px solid var(--color-slate-200); border-top: 1px solid var(--color-slate-200); border-bottom: 1px solid var(--color-slate-200); }
    .stInfo { background: #F0F9FF; border-left: 3px solid var(--color-info) !important; border-right: 1px solid var(--color-slate-200); border-top: 1px solid var(--color-slate-200); border-bottom: 1px solid var(--color-slate-200); }

    .stMetric { background: var(--color-slate-50); border: 1px solid var(--color-slate-200); padding: 1.5rem; border-radius: 0.75rem; text-align: center; }
    .stMetric label { font-size: 0.75rem; color: var(--color-slate-600); font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
    .stMetric [data-testid="metric-value"] { font-size: 2rem; font-weight: 800; color: var(--color-primary); margin-top: 0.75rem; }

    h1 { font-size: 2rem; font-weight: 800; color: var(--color-slate-900); margin: 1.5rem 0 1rem 0; letter-spacing: -0.02em; }
    h2 { font-size: 1.5rem; font-weight: 700; color: var(--color-slate-900); margin: 1.25rem 0 0.75rem 0; }
    h3 { font-size: 1.125rem; font-weight: 700; color: var(--color-slate-800); margin: 1rem 0 0.5rem 0; }
    h4 { font-size: 1rem; font-weight: 600; color: var(--color-slate-800); margin: 0.75rem 0 0.5rem 0; }

    body, p { color: var(--color-slate-700); line-height: 1.6; }
    a { color: var(--color-primary); text-decoration: none; font-weight: 600; }
    a:hover { text-decoration: underline; color: var(--color-primary-dark); }

    .stExpander { border: 1px solid var(--color-slate-200); border-radius: 0.625rem; background: #FFFFFF; }
    .stExpander [data-testid="stExpanderDetails"] { background: var(--color-slate-50); }
    
    /* FIX: Clean spacing */
    .stDivider { background-color: var(--color-slate-200); height: 1px; margin: 1.5rem 0 !important; }
    [data-testid="column"] { gap: 1.5rem; }

    .answer-box { background: linear-gradient(135deg, var(--color-primary-light) 0%, #FFFFFF 100%); padding: 1.75rem; border-radius: 0.75rem; border-left: 4px solid var(--color-primary); font-size: 1.0625rem; line-height: 1.8; color: var(--color-slate-900); margin: 1rem 0; }

    .nav-section-title { font-size: 0.75rem; font-weight: 700; color: var(--color-slate-600); text-transform: uppercase; letter-spacing: 0.05em; padding: 0.5rem 1rem; margin-bottom: 0.5rem; }
    .nav-item { padding: 0.75rem 1rem; margin: 0.25rem 0; border-radius: 0.5rem; cursor: pointer; transition: all 0.2s; color: var(--color-slate-700); font-weight: 500; }
    .nav-item:hover { background: var(--color-slate-100); color: var(--color-primary); }
    .nav-item-active { background: var(--color-primary-light); color: var(--color-primary); font-weight: 600; }

    [data-testid="stSidebar"] { background: linear-gradient(180deg, #FFFFFF 0%, var(--color-slate-50) 100%); border-right: 1px solid var(--color-slate-200); }

    /* FIX: Footer spacing */
    .footer-section { margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid var(--color-slate-200); }
    .footer-links { display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap; text-align: center; }
    .footer-link { font-size: 0.875rem; color: var(--color-slate-600); }

    @media (max-width: 768px) { 
        [data-testid="stMain"] { padding: 1rem 1.5rem !important; }
        .page-title { font-size: 1.75rem; }
        .footer-links { gap: 1rem; }
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
    
    if st.button("💬 Chat & Ask", use_container_width=True, key="nav_chat"):
        st.session_state.current_page = "chat"
        st.rerun()
    
    if st.button("📤 Upload", use_container_width=True, key="nav_upload"):
        st.session_state.current_page = "upload"
        st.rerun()
    
    if st.button("📋 Library", use_container_width=True, key="nav_docs"):
        st.session_state.current_page = "documents"
        st.rerun()
    
    st.divider()
    st.markdown('<div class="nav-section-title">⚙️ Tools</div>', unsafe_allow_html=True)
    
    if st.button("🔧 Settings", use_container_width=True, key="nav_settings"):
        st.session_state.current_page = "settings"
        st.rerun()

# ============================================================================
# PAGE HEADER
# ============================================================================
st.markdown(
    """
    <div class="page-header">
        <h1 class="page-title">📚 Chat With Documents</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================================
# PAGES WITH FIXED LAYOUT AND ALIGNMENT
# ============================================================================

if st.session_state.current_page == "chat":
    st.markdown("### 💬 Ask Questions About Your Documents")
    st.divider()
    
    # FIX: Proper column layout for input and button alignment
    form_col1, form_col2 = st.columns([4, 1], gap="medium")
    
    with form_col1:
        query = st.text_area(
            "Your question",
            placeholder="Ask about your documents...",
            height=110,
            key="chat_query",
        )
    
    with form_col2:
        st.write("")
        st.write("")
        ask_button = st.button(
            "🚀 Ask",
            use_container_width=True,
            type="primary",
            key="ask_btn"
        )
    
    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
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
                    
                    st.markdown("**📝 Answer**")
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
                        st.markdown("**📎 Source Documents**")
                        for i, source in enumerate(response["sources"], 1):
                            with st.expander(
                                f"Document {i}: {source.get('filename', 'Unknown')} - Page {source.get('page_number')}"
                            ):
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.write(source.get("text_preview", "")[:400])
                                with col2:
                                    st.metric("Match", f"{source.get('similarity_score', 0):.0%}")
                
                except Exception as e:
                    st.toast(f"Error: {str(e)}", icon="❌")
    
    # Chat history
    if st.session_state.chat_history:
        st.divider()
        st.markdown("**📜 Chat History**")
        for i, item in enumerate(st.session_state.chat_history[:5]):
            with st.expander(f"{i+1}. {item.get('query', '')[:60]}...", expanded=False):
                st.write(f"**Q:** {item.get('query', '')}")
                st.write(f"**A:** {item.get('answer', '')[:300]}...")
                st.caption(f"{len(item.get('sources', []))} sources used")

elif st.session_state.current_page == "upload":
    st.markdown("### 📤 Upload PDF Documents")
    st.caption("Upload your PDF documents to be indexed and searchable")
    st.divider()
    
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf", help="Max 10MB, max 100 pages")
    
    if uploaded_file is not None:
        st.divider()
        file_size_mb = uploaded_file.size / 1024 / 1024
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Filename", uploaded_file.name[:20] + "..." if len(uploaded_file.name) > 20 else uploaded_file.name)
        with col2:
            st.metric("File Size", f"{file_size_mb:.2f} MB")
        with col3:
            st.metric("Status", "✓ Ready")
        with col4:
            st.metric("Format", "PDF")
        
        st.divider()
        col1, col2 = st.columns([4, 1])
        with col2:
            upload_button = st.button("Upload & Index", use_container_width=True, type="primary")
        
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
            <div class="card" style="margin-top: 2rem;">
                <div class="card-header">📋 Upload Guidelines</div>
                
                **Supported Format:**
                - PDF documents only
                
                **File Limits:**
                - Maximum: 10 MB
                - Maximum pages: 100
                
                **Processing:**
                - Automatic text extraction
                - Smart page chunking
                - Semantic indexing
                - Instant searchability
            </div>
            """,
            unsafe_allow_html=True,
        )

elif st.session_state.current_page == "documents":
    st.markdown("### 📋 Document Library")
    st.caption("View and manage all indexed documents")
    
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
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
                    st.markdown("**Documents**")
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
    st.markdown("### ⚙️ System Settings & Information")
    st.divider()
    
    st.markdown("**🏥 System Health**")
    try:
        health = api_client.check_health()
        col1, col2, col3 = st.columns(3)
        with col1:
            status_icon = "🟢" if health.get("status") == "healthy" else "🟡"
            st.metric("API Status", f"{status_icon} {health.get('status', 'unknown').title()}")
        with col2:
            st.metric("API Version", health.get("version", "?"))
        with col3:
            st.metric("Last Check", health.get("timestamp", "?")[:10])
    except Exception as e:
        st.toast(f"Could not connect: {str(e)}", icon="❌")
    
    st.divider()
    st.markdown("**⚙️ Configuration**")
    
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
    st.markdown("**ℹ️ About**")
    st.markdown(
        """
        **Chat With Documents** is an enterprise RAG system.
        
        **Features:** PDF ingestion • Semantic search • AI Q&A • Source citations • Privacy-first
        
        **Tech:** FastAPI • Streamlit • ChromaDB • Ollama | **Version:** 0.1.0
        """
    )

# ============================================================================
# FOOTER WITH PROPER SPACING
# ============================================================================
# Footer links removed for cleaner interface
