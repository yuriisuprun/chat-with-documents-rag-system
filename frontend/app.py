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
        /* Colors - Accessible contrast ratios */
        --primary: #6366F1;          /* Indigo - vibrant, modern */
        --primary-hover: #4F46E5;    /* Darker for interactions */
        --primary-light: #EEF2FF;    /* Very light for backgrounds */
        --primary-dark: #3730A3;     /* For strong contrast text */
        --text: #0F172A;             /* Dark slate - excellent contrast */
        --text-secondary: #475569;   /* Mid slate */
        --text-tertiary: #94A3B8;    /* Light slate */
        --success: #10B981;          /* Green for positive actions */
        --warning: #F59E0B;          /* Amber for alerts */
        --error: #EF4444;            /* Red for errors */
        --border: #E2E8F0;           /* Light border */
        --bg: #FFFFFF;               /* Pure white for content */
        --bg-secondary: #F8FAFC;     /* Very light gray for app background */
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        --radius: 0.75rem;           /* Consistent border radius */
        --spacing-xs: 0.25rem;
        --spacing-sm: 0.5rem;
        --spacing-md: 1rem;
        --spacing-lg: 1.5rem;
        --spacing-xl: 2rem;
        --spacing-2xl: 3rem;
    }

    /* Base typography - minimum 16px for readability */
    html, body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 16px;
        line-height: 1.6;
        background: var(--bg-secondary);
        color: var(--text);
    }

    /* Global elements */
    * {
        font-family: inherit;
    }

    /* Streamlit overrides */
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

    /* Main container - centered with max width */
    .main-container {
        max-width: 56rem;
        margin: 0 auto;
        padding: 1rem 1.5rem 2rem 1.5rem;
    }

    /* Typography hierarchy */
    h1, .h1 {
        font-size: 2.5rem;
        font-weight: 700;
        line-height: 1.2;
        margin: 0 0 var(--spacing-md) 0;
        color: var(--text);
        letter-spacing: -0.02em;
    }

    h2, .h2 {
        font-size: 1.875rem;
        font-weight: 700;
        line-height: 1.3;
        margin: 0 0 var(--spacing-md) 0;
        color: var(--text);
    }

    h3, .h3 {
        font-size: 1.5rem;
        font-weight: 600;
        margin: 0 0 var(--spacing-sm) 0;
        color: var(--text);
    }

    p, .body-text {
        font-size: 1.125rem;
        line-height: 1.6;
        margin: 0 0 var(--spacing-md) 0;
        color: var(--text-secondary);
    }

    .subtitle {
        font-size: 1.125rem;
        line-height: 1.6;
        color: var(--text-secondary);
    }

    .caption-text {
        font-size: 0.95rem;
        line-height: 1.5;
        color: var(--text-tertiary);
    }

    /* Header section */
    .header {
        margin-bottom: 3rem;
    }

    .header h1 {
        margin-bottom: 0.75rem;
        font-size: 2.5rem;
    }

    .header p {
        margin: 0;
        font-size: 1.125rem;
    }

    /* Card containers */
    .card {
        background: var(--bg);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: var(--spacing-lg);
        box-shadow: var(--shadow-sm);
        transition: all 0.2s ease;
    }

    .card:hover {
        box-shadow: var(--shadow-md);
    }

    /* Chat container */
    .chat-container {
        background: var(--bg);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.5rem;
        margin-bottom: 2rem;
        box-shadow: var(--shadow-sm);
        transition: all 0.2s ease;
    }

    .chat-container:hover {
        box-shadow: var(--shadow-md);
    }

    /* Textarea */
    .stTextArea {
        margin: 1.5rem 0 1.5rem 0 !important;
    }

    .stTextArea textarea {
        font-size: 1.125rem !important;
        border: 2px solid var(--border) !important;
        border-radius: 0.625rem !important;
        padding: var(--spacing-md) !important;
        transition: all 0.2s ease !important;
        background: var(--bg) !important;
        color: var(--text) !important;
        line-height: 1.6 !important;
        min-height: 120px !important;
    }

    .stTextArea textarea:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 4px var(--primary-light) !important;
        outline: none !important;
    }

    .stTextArea textarea::placeholder {
        color: var(--text-tertiary);
        font-size: 1.125rem;
    }

    /* Buttons - Large, accessible touch targets */
    .stButton {
        margin: 0 !important;
    }

    .stButton button {
        font-size: 1.125rem !important;
        font-weight: 600 !important;
        padding: 1rem 2rem !important;
        border-radius: 0.625rem !important;
        border: none !important;
        transition: all 0.2s ease !important;
        letter-spacing: -0.01em !important;
        cursor: pointer !important;
        min-height: 52px !important;
        line-height: 1.5 !important;
    }

    .stButton button[kind="primary"] {
        background: var(--primary) !important;
        color: white !important;
        box-shadow: var(--shadow-sm) !important;
    }

    .stButton button[kind="primary"]:hover {
        background: var(--primary-hover) !important;
        box-shadow: var(--shadow-md) !important;
        transform: translateY(-1px);
    }

    .stButton button[kind="primary"]:focus {
        outline: 3px solid var(--primary-light) !important;
        outline-offset: 2px !important;
    }

    .stButton button[kind="secondary"] {
        background: var(--bg-secondary) !important;
        color: var(--text) !important;
        border: 2px solid var(--border) !important;
    }

    .stButton button[kind="secondary"]:hover {
        background: var(--border) !important;
        border-color: var(--text-secondary) !important;
    }

    .stButton button[kind="secondary"]:focus {
        outline: 3px solid var(--primary-light) !important;
        outline-offset: 2px !important;
    }

    /* Answer box with left accent */
    .answer-box {
        background: linear-gradient(135deg, var(--primary-light) 0%, var(--bg) 100%);
        border-left: 5px solid var(--primary);
        padding: var(--spacing-lg);
        border-radius: var(--radius);
        margin: var(--spacing-lg) 0;
        line-height: 1.8;
        color: var(--text);
        box-shadow: var(--shadow-sm);
        font-size: 1.125rem;
    }

    .answer-box strong {
        color: var(--text);
        font-weight: 600;
    }

    /* Expandable sections */
    .stExpander {
        border: 1px solid var(--border) !important;
        border-radius: 0.625rem !important;
        background: var(--bg) !important;
        margin: var(--spacing-md) 0 !important;
        box-shadow: var(--shadow-sm) !important;
    }

    /* File uploader - prominent drop zone */
    [data-testid="stFileUploader"] {
        border: 2px dashed var(--border) !important;
        border-radius: var(--radius) !important;
        padding: var(--spacing-2xl) var(--spacing-lg) !important;
        background: var(--bg) !important;
        transition: all 0.2s ease !important;
        cursor: pointer;
    }

    [data-testid="stFileUploader"]:hover {
        border-color: var(--primary) !important;
        background: var(--primary-light) !important;
    }

    /* Metrics - Large, readable numbers */
    .stMetric {
        background: var(--bg);
        border: 1px solid var(--border);
        padding: var(--spacing-md);
        border-radius: 0.625rem;
        box-shadow: var(--shadow-sm);
    }

    .stMetric label {
        font-size: 0.95rem !important;
        color: var(--text-tertiary) !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: var(--spacing-xs) !important;
    }

    .stMetric [data-testid="metric-value"] {
        color: var(--text) !important;
        font-weight: 700 !important;
        font-size: 2.25rem !important;
        line-height: 1.2 !important;
    }

    /* Sidebar - Navigation area */
    [data-testid="stSidebar"] {
        background: var(--bg);
        border-right: 1px solid var(--border);
        padding: var(--spacing-lg) var(--spacing-md) !important;
    }

    [data-testid="stSidebar"] .stButton {
        margin-bottom: 1rem !important;
    }

    [data-testid="stSidebar"] .stButton button {
        font-size: 1.125rem !important;
        padding: 1rem 1.25rem !important;
        justify-content: flex-start !important;
        text-align: left !important;
        width: 100% !important;
        height: 52px !important;
    }

    /* Sidebar typography */
    [data-testid="stSidebar"] h3 {
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        margin: 0 0 var(--spacing-sm) 0 !important;
        color: var(--text);
    }

    [data-testid="stSidebar"] .stCaption {
        font-size: 1rem !important;
        color: var(--text-secondary) !important;
        line-height: 1.5 !important;
    }

    /* Dividers */
    .stDivider {
        margin: 1.5rem 0 !important;
        border-color: var(--border) !important;
    }

    /* Empty state - Centered, friendly messaging */
    .empty-state {
        text-align: center;
        padding: 3rem 1.5rem;
        background: var(--bg);
        border: 2px dashed var(--border);
        border-radius: var(--radius);
        margin: 2rem 0;
        color: var(--text-secondary);
    }

    .empty-state-icon {
        font-size: 4rem;
        margin-bottom: 1.5rem;
        opacity: 0.4;
    }

    .empty-state p {
        font-size: 1.125rem;
        margin: var(--spacing-sm) 0;
        line-height: 1.6;
    }

    .empty-state p strong {
        color: var(--text);
        font-weight: 600;
    }

    .empty-state p.hint {
        font-size: 1rem;
        color: var(--text-tertiary);
    }

    /* Utility classes */
    .text-secondary {
        color: var(--text-secondary);
    }

    .text-tertiary {
        color: var(--text-tertiary);
    }

    .text-success {
        color: var(--success);
    }

    .text-error {
        color: var(--error);
    }

    /* Hide Streamlit branding */
    .stDeployButton {
        display: none;
    }

    footer {
        display: none;
    }

    #MainMenu {
        display: none;
    }

    /* Focus states for accessibility */
    button:focus-visible,
    input:focus-visible,
    textarea:focus-visible,
    a:focus-visible {
        outline: 3px solid var(--primary);
        outline-offset: 2px;
    }

    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .main-container {
            padding: var(--spacing-lg) var(--spacing-md);
        }

        h1, .h1 {
            font-size: 2rem;
        }

        h2, .h2 {
            font-size: 1.5rem;
        }

        p, .body-text {
            font-size: 1rem;
        }

        .stButton button {
            font-size: 1rem !important;
            padding: 0.875rem 1.5rem !important;
        }

        .stTextArea textarea {
            font-size: 1rem !important;
        }
    }

    /* Dark mode support (if needed in future) */
    @media (prefers-color-scheme: dark) {
        /* Can be extended with dark mode colors */
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

    # Status indicator at bottom
    st.divider()
    try:
        health = api_client.check_health()
        status = (
            "🟢 Connected" if health.get("status") == "healthy" else "🟡 Limited"
        )
        st.caption(status)
    except:
        st.caption("🔴 Disconnected")

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
