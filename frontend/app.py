"""
Chat With Documents - Modern UI Following 2026 UX/UI Best Practices

Clean, minimal design with proper visual hierarchy, typography, spacing,
accessibility, and user-centered interactions.
"""

import os
import sys
from pathlib import Path
import streamlit as st

# Add backend to Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.config import settings

# Page config - wider layout for better readability
st.set_page_config(
    page_title="Chat With Documents",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# MODERN UI/UX DESIGN - 2026 Best Practices
# ============================================================================
def load_modern_css():
    """
    Modern design following 2026 UX/UI best practices:
    - Large, readable typography (min 16px)
    - Generous whitespace and padding
    - Clear visual hierarchy
    - Accessible color contrasts
    - Smooth transitions and micro-interactions
    - Mobile-responsive design
    - Focus states for keyboard navigation
    """
    css = """
    <style>
    :root {
        /* Modern color palette */
        --primary: #5B21B6;          /* Deep purple - premium feel */
        --primary-hover: #7C3AED;    /* Brighter purple on hover */
        --primary-light: #EDE9FE;    /* Very light purple */
        --accent: #3B82F6;           /* Bright blue for accents */
        --text: #1F2937;             /* Dark gray */
        --text-secondary: #6B7280;   /* Medium gray */
        --text-tertiary: #9CA3AF;    /* Light gray */
        --success: #10B981;          /* Green */
        --warning: #F59E0B;          /* Amber */
        --error: #EF4444;            /* Red */
        --border: #E5E7EB;           /* Light border */
        --bg: #FFFFFF;               /* White */
        --bg-secondary: #F9FAFB;     /* Off-white */
        --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        --shadow-md: 0 4px 12px 0 rgba(0, 0, 0, 0.08);
        --shadow-lg: 0 10px 25px 0 rgba(0, 0, 0, 0.1);
        --radius: 0.5rem;
    }

    html, body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 16px;
        line-height: 1.6;
        background: var(--bg-secondary);
        color: var(--text);
    }

    * {
        font-family: inherit;
    }

    [data-testid="stAppViewContainer"] {
        background: var(--bg-secondary);
    }

    [data-testid="stMain"] {
        padding: 0 !important;
        background: var(--bg-secondary);
    }

    .stApp > header {
        display: none !important;
    }

    .main-container {
        max-width: 52rem;
        margin: 0 auto;
        padding: 0.5rem 1.5rem 2rem 1.5rem;
    }

    h1, .h1 {
        font-size: 2rem;
        font-weight: 800;
        line-height: 1.2;
        margin: 0 0 0.5rem 0;
        color: var(--text);
        letter-spacing: -0.02em;
    }

    h2, .h2 {
        font-size: 1.5rem;
        font-weight: 700;
        line-height: 1.3;
        margin: 0 0 0.5rem 0;
        color: var(--text);
    }

    p, .body-text {
        font-size: 1rem;
        line-height: 1.6;
        margin: 0 0 1rem 0;
        color: var(--text-secondary);
    }

    .subtitle {
        font-size: 1rem;
        line-height: 1.6;
        color: var(--text-secondary);
        margin: 0;
    }

    .header {
        margin-bottom: 2rem;
    }

    .header h1 {
        margin-bottom: 0.5rem;
    }

    .card {
        background: var(--bg);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.5rem;
        box-shadow: var(--shadow-sm);
        transition: all 0.2s ease;
    }

    .card:hover {
        box-shadow: var(--shadow-md);
        border-color: var(--primary);
    }

    .chat-container {
        background: var(--bg);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: var(--shadow-sm);
        transition: all 0.2s ease;
    }

    .chat-container:hover {
        box-shadow: var(--shadow-md);
    }

    .stTextArea {
        margin: 1rem 0 !important;
    }

    .stTextArea textarea {
        font-size: 1rem !important;
        border: 2px solid var(--border) !important;
        border-radius: 0.5rem !important;
        padding: 0.75rem !important;
        transition: all 0.2s ease !important;
        background: var(--bg) !important;
        color: var(--text) !important;
        line-height: 1.6 !important;
        min-height: 100px !important;
    }

    .stTextArea textarea:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(91, 33, 182, 0.1) !important;
        outline: none !important;
    }

    .stTextArea textarea::placeholder {
        color: var(--text-tertiary);
        font-size: 1rem;
    }

    .stButton {
        margin: 0 !important;
    }

    .stButton button {
        font-size: 1rem !important;
        font-weight: 700 !important;
        padding: 0.75rem 1.5rem !important;
        border-radius: 0.5rem !important;
        border: none !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
        min-height: 44px !important;
    }

    .stButton button[kind="primary"] {
        background: var(--primary) !important;
        color: #FFFFFF !important;
        box-shadow: var(--shadow-sm) !important;
        font-weight: 700 !important;
    }

    .stButton button[kind="primary"] > * {
        color: #FFFFFF !important;
    }

    .stButton button[kind="primary"] p,
    .stButton button[kind="primary"] span,
    .stButton button[kind="primary"] div {
        color: #FFFFFF !important;
    }

    .stButton button[kind="primary"]:hover {
        background: var(--primary-hover) !important;
        box-shadow: var(--shadow-md) !important;
        transform: translateY(-1px);
    }

    .stButton button[kind="secondary"] {
        background: var(--bg) !important;
        color: #1F2937 !important;
        border: 1.5px solid var(--border) !important;
        font-weight: 700 !important;
    }

    .stButton button[kind="secondary"] > * {
        color: #1F2937 !important;
    }

    .stButton button[kind="secondary"] p,
    .stButton button[kind="secondary"] span,
    .stButton button[kind="secondary"] div {
        color: #1F2937 !important;
    }

    .stButton button[kind="secondary"]:hover {
        background: var(--bg-secondary) !important;
        border-color: var(--primary) !important;
        color: var(--primary) !important;
    }

    .answer-box {
        background: linear-gradient(135deg, var(--primary-light) 0%, var(--bg) 100%);
        border-left: 4px solid var(--primary);
        padding: 1.25rem;
        border-radius: var(--radius);
        margin: 1.5rem 0;
        line-height: 1.7;
        color: var(--text);
        box-shadow: var(--shadow-sm);
        font-size: 1rem;
    }

    .stExpander {
        border: 1px solid var(--border) !important;
        border-radius: 0.5rem !important;
        background: var(--bg) !important;
        margin: 1rem 0 !important;
        box-shadow: var(--shadow-sm) !important;
    }

    [data-testid="stFileUploader"] {
        border: 2px dashed var(--border) !important;
        border-radius: var(--radius) !important;
        padding: 2rem 1.5rem !important;
        background: var(--bg) !important;
        transition: all 0.2s ease !important;
    }

    [data-testid="stFileUploader"]:hover {
        border-color: var(--primary) !important;
        background: var(--primary-light) !important;
    }

    .stMetric {
        background: var(--bg);
        border: 1px solid var(--border);
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: var(--shadow-sm);
    }

    .stMetric label {
        font-size: 0.875rem !important;
        color: var(--text-tertiary) !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    .stMetric [data-testid="metric-value"] {
        color: var(--primary) !important;
        font-weight: 700 !important;
        font-size: 1.75rem !important;
    }

    [data-testid="stSidebar"] {
        background: var(--bg);
        border-right: 1px solid var(--border);
        padding: 1.5rem 1rem !important;
    }

    [data-testid="stSidebar"] .stButton {
        margin-bottom: 0.75rem !important;
    }

    [data-testid="stSidebar"] .stButton button {
        font-size: 1rem !important;
        padding: 0.875rem 1rem !important;
        justify-content: flex-start !important;
        text-align: left !important;
        width: 100% !important;
        height: 44px !important;
    }

    [data-testid="stSidebar"] h3 {
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        margin: 0 0 0.5rem 0 !important;
        color: var(--text);
    }

    [data-testid="stSidebar"] .stCaption {
        font-size: 0.875rem !important;
        color: var(--text-secondary) !important;
    }

    .stDivider {
        margin: 1rem 0 !important;
        border-color: var(--border) !important;
    }

    .empty-state {
        text-align: center;
        padding: 2rem 1.5rem;
        background: var(--bg);
        border: 2px dashed var(--border);
        border-radius: var(--radius);
        margin: 1.5rem 0;
        color: var(--text-secondary);
    }

    .empty-state-icon {
        font-size: 3.5rem;
        margin-bottom: 1rem;
        opacity: 0.3;
    }

    .empty-state p {
        font-size: 1rem;
        margin: 0.5rem 0;
        line-height: 1.5;
    }

    .empty-state p strong {
        color: var(--text);
        font-weight: 600;
    }

    .empty-state p.hint {
        font-size: 0.925rem;
        color: var(--text-tertiary);
    }

    .stDeployButton { display: none; }
    footer { display: none; }
    #MainMenu { display: none; }

    @media (max-width: 768px) {
        .main-container { padding: 1rem; }
        h1, .h1 { font-size: 1.5rem; }
        .stButton button { font-size: 0.95rem !important; }
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

load_modern_css()

# Import API client
from api_client import APIClient

@st.cache_resource
def get_api_client():
    host = settings.api_host if settings.api_host != "0.0.0.0" else "localhost"
    api_url = os.getenv("API_URL", f"http://{host}:{settings.api_port}")
    return APIClient(api_url)

api_client = get_api_client()

# ============================================================================
# SIDEBAR - Navigation
# ============================================================================
with st.sidebar:
    st.markdown("### Documents")
    st.caption("AI-powered document Q&A")
    st.divider()

    if "page" not in st.session_state:
        st.session_state.page = "chat"

    # Navigation buttons
    if st.button(
        "Chat",
        width="stretch",
        type="primary" if st.session_state.page == "chat" else "secondary",
        key="nav_chat",
    ):
        st.session_state.page = "chat"
        st.rerun()

    if st.button(
        "Upload",
        width="stretch",
        type="primary" if st.session_state.page == "upload" else "secondary",
        key="nav_upload",
    ):
        st.session_state.page = "upload"
        st.rerun()

    if st.button(
        "Library",
        width="stretch",
        type="primary" if st.session_state.page == "library" else "secondary",
        key="nav_library",
    ):
        st.session_state.page = "library"
        st.rerun()

# ============================================================================
# MAIN CONTENT
# ============================================================================

# ----- CHAT PAGE -----
if st.session_state.page == "chat":
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    # Header
    st.markdown(
        """
        <div class="header">
            <h1>Ask Your Documents</h1>
            <p class="subtitle">Get instant answers with source citations from your knowledge base</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    # Chat history
    if "history" not in st.session_state:
        st.session_state.history = []

    # Show recent answers
    if st.session_state.history:
        for idx, item in enumerate(st.session_state.history[:3]):
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)

            # Question
            st.markdown(f"**Q:** {item['query']}")
            st.divider()

            # Answer
            st.markdown(
                f'<div class="answer-box">{item["answer"]}</div>',
                unsafe_allow_html=True,
            )

            # Sources
            if item.get("sources"):
                with st.expander(
                    f"📎 Sources ({len(item['sources'])})",
                    expanded=False,
                ):
                    for i, src in enumerate(item["sources"], 1):
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(
                                f"**{src.get('filename')}** · Page {src.get('page_number')}"
                            )
                            st.caption(
                                src.get("text_preview", "")[:200] + "..."
                            )
                        with col2:
                            st.metric(
                                "Match",
                                f"{src.get('similarity_score', 0):.0%}",
                            )
                        if i < len(item["sources"]):
                            st.divider()

            st.markdown("</div>", unsafe_allow_html=True)
    else:
        # Empty state
        st.markdown(
            """
            <div class="empty-state">
                <div class="empty-state-icon">💬</div>
                <p><strong>No conversations yet</strong></p>
                <p class="hint">Ask your first question below to get started</p>
            </div>
        """,
            unsafe_allow_html=True,
        )

    # Input area
    query = st.text_area(
        "Ask a question",
        placeholder="What would you like to know about your documents?",
        height=120,
        key="chat_input",
        label_visibility="collapsed",
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        send_btn = st.button(
            "Send", width="stretch", type="primary", key="send_btn"
        )
    with col2:
        if st.session_state.history:
            if st.button("Clear", width="stretch", type="secondary", key="clear_btn"):
                st.session_state.history = []
                st.rerun()

    # Handle send action
    if send_btn and query.strip():
        with st.spinner("Thinking..."):
            try:
                response = api_client.ask_question(query)
                st.session_state.history.insert(
                    0,
                    {
                        "query": query,
                        "answer": response.get("answer", ""),
                        "sources": response.get("sources", []),
                    },
                )
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")

    st.markdown("</div>", unsafe_allow_html=True)

# ----- UPLOAD PAGE -----
elif st.session_state.page == "upload":
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    # Header
    st.markdown(
        """
        <div class="header">
            <h1>Upload Documents</h1>
            <p class="subtitle">Add PDF files to build your searchable knowledge base</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Drag and drop or click to browse",
        type="pdf",
        help="Supported: PDF · Max 10MB, 100 pages",
        label_visibility="collapsed",
    )

    if uploaded:
        st.divider()

        # File info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Filename",
                uploaded.name[:20] + "..." if len(uploaded.name) > 20 else uploaded.name,
            )
        with col2:
            st.metric("Size", f"{uploaded.size / 1024 / 1024:.2f} MB")
        with col3:
            st.metric("Type", "PDF")

        st.divider()

        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button(
                "Upload & Index", width="stretch", type="primary", key="upload_btn"
            ):
                with st.spinner("Processing document..."):
                    try:
                        response = api_client.upload_document(uploaded)
                        st.success("✅ Document uploaded successfully!")
                        st.info(
                            f"📊 Indexed **{response.get('chunk_count')}** chunks from **{response.get('page_count')}** pages"
                        )
                        st.markdown("💬 Go to **Chat** to start asking questions")
                    except Exception as e:
                        st.error(f"Upload failed: {str(e)}")
    else:
        # Guidelines
        st.markdown(
            """
            **📋 Upload Guidelines**

            - **Format:** PDF documents only
            - **Size limit:** 10 MB maximum
            - **Page limit:** 100 pages maximum
            - **Processing:** Automatic text extraction and semantic indexing
            - **Privacy:** Documents are stored locally and never shared
        """
        )

    st.markdown("</div></div>", unsafe_allow_html=True)

# ----- LIBRARY PAGE -----
elif st.session_state.page == "library":
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    # Header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(
            """
            <div class="header">
                <h1>Document Library</h1>
                <p class="subtitle">Manage and organize your indexed documents</p>
            </div>
        """,
            unsafe_allow_html=True,
        )
    with col2:
        st.write("")  # Spacing
        if st.button("🔄 Refresh", width="stretch", type="secondary", key="refresh_btn"):
            st.rerun()

    try:
        docs = api_client.list_documents()

        if docs.get("count", 0) > 0:
            # Stats
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Documents", len(docs.get("documents", [])))
            with col2:
                st.metric("Total Chunks", docs.get("count", 0))
            st.markdown("</div>", unsafe_allow_html=True)

            # Document list
            for doc in docs.get("documents", []):
                st.markdown('<div class="chat-container">', unsafe_allow_html=True)

                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 0.6])
                with col1:
                    st.markdown(f"**{doc.get('filename')}**")
                with col2:
                    st.caption(f"📄 {doc.get('page_count', 0)} pages")
                with col3:
                    st.caption(f"📊 {doc.get('chunk_count', 0)} chunks")
                with col4:
                    size_mb = doc.get("size_mb", 0)
                    st.caption(f"💾 {size_mb:.1f} MB" if size_mb else "N/A")
                with col5:
                    if st.button(
                        "Delete", key=f"del_{doc.get('id')}", type="secondary"
                    ):
                        with st.spinner("Deleting..."):
                            try:
                                api_client.delete_document(doc.get("id"))
                                st.success("Document deleted")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed: {str(e)}")

                st.markdown("</div>", unsafe_allow_html=True)
        else:
            # Empty state
            st.markdown(
                """
                <div class="empty-state">
                    <div class="empty-state-icon">📚</div>
                    <p><strong>No documents in your library yet</strong></p>
                    <p class="hint">Upload PDF files to build your knowledge base</p>
                </div>
            """,
                unsafe_allow_html=True,
            )
    except Exception as e:
        st.error(f"Error loading documents: {str(e)}")

    st.markdown("</div>", unsafe_allow_html=True)
