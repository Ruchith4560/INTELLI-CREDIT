"""
╔══════════════════════════════════════════════════════════════════╗
║  Intelli-Credit — RAG Regulatory Knowledge Base                 ║
║                                                                  ║
║  HOW TO ENABLE:                                                  ║
║    1. pip install langchain langchain-community faiss-cpu        ║
║                  sentence-transformers PyMuPDF                   ║
║    2. Download RBI/GST PDFs into:  backend/knowledge_base/       ║
║       e.g. RBI_NBFC_Guidelines.pdf, GST_Circular_2024.pdf       ║
║       Source: https://rbi.org.in/Scripts/BS_PressReleaseDisplay ║
║    3. Call load_knowledge_base() on startup (optional)           ║
║    4. Call query_regulations(question) in analysis pipeline      ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── Module-level cache ────────────────────────────────────────────────────────
_vectorstore = None
_embeddings  = None

KB_PATH       = "knowledge_base"
INDEX_PATH    = "knowledge_base/faiss_index"
EMBED_MODEL   = "sentence-transformers/all-MiniLM-L6-v2"   # free, local, fast


# ─────────────────────────────────────────────────────────────────────────────
# LOAD KNOWLEDGE BASE  (call once on startup)
# ─────────────────────────────────────────────────────────────────────────────

def load_knowledge_base(force_rebuild: bool = False):
    """
    Loads RBI/GST documents from knowledge_base/ into a FAISS vector store.
    Builds the index from PDFs if not cached; loads cached index otherwise.

    Returns the vector store, or None if not available.
    """
    global _vectorstore, _embeddings

    if _vectorstore is not None and not force_rebuild:
        return _vectorstore

    # Check if knowledge_base directory exists and has PDFs
    if not os.path.exists(KB_PATH):
        os.makedirs(KB_PATH, exist_ok=True)
        logger.warning(f"⚠️  knowledge_base/ folder created but is empty.")
        logger.warning("    Add RBI/GST PDF files to enable RAG functionality.")
        return None

    pdf_files = [f for f in os.listdir(KB_PATH) if f.endswith(".pdf")]
    if not pdf_files:
        logger.warning("⚠️  No PDF files in knowledge_base/ — RAG disabled.")
        return None

    try:
        from langchain_community.document_loaders  import PyPDFDirectoryLoader
        from langchain.text_splitter               import RecursiveCharacterTextSplitter
        from langchain_community.embeddings        import HuggingFaceEmbeddings
        from langchain_community.vectorstores      import FAISS

        logger.info(f"📚 Loading {len(pdf_files)} regulatory documents from knowledge_base/...")

        # Load all PDFs
        loader = PyPDFDirectoryLoader(KB_PATH)
        docs   = loader.load()
        logger.info(f"   Loaded {len(docs)} pages from {len(pdf_files)} PDFs")

        # Split into chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ".", " "],
        )
        chunks = splitter.split_documents(docs)
        logger.info(f"   Split into {len(chunks)} chunks")

        # Create embeddings (runs locally — no API cost)
        _embeddings = HuggingFaceEmbeddings(
            model_name=EMBED_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

        # Load or rebuild FAISS index
        if os.path.exists(INDEX_PATH) and not force_rebuild:
            logger.info("   Loading cached FAISS index...")
            _vectorstore = FAISS.load_local(
                INDEX_PATH, _embeddings, allow_dangerous_deserialization=True
            )
        else:
            logger.info("   Building FAISS index (first time may take ~30 seconds)...")
            _vectorstore = FAISS.from_documents(chunks, _embeddings)
            _vectorstore.save_local(INDEX_PATH)
            logger.info(f"   Index saved to {INDEX_PATH}")

        logger.info("✅ RAG Knowledge Base ready")
        return _vectorstore

    except ImportError as e:
        logger.warning(
            f"⚠️  RAG dependencies not installed: {e}\n"
            "    Run: pip install langchain langchain-community faiss-cpu sentence-transformers"
        )
        return None
    except Exception as e:
        logger.error(f"RAG load error: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# QUERY REGULATIONS
# ─────────────────────────────────────────────────────────────────────────────

def query_regulations(question: str, k: int = 3) -> str:
    """
    Retrieves relevant regulatory context for a given question.
    Used to inject RBI/GST rules into the LLM credit explanation.

    Args:
        question: e.g. "RBI guidelines for NBFC lending limit"
        k:        number of relevant chunks to retrieve

    Returns:
        A string of relevant regulatory text, or empty string if unavailable.
    """
    store = load_knowledge_base()
    if store is None:
        return ""

    try:
        docs    = store.similarity_search(question, k=k)
        context = "\n\n---\n\n".join([d.page_content for d in docs])
        logger.info(f"✅ RAG retrieved {len(docs)} chunks for: '{question[:60]}...'")
        return context
    except Exception as e:
        logger.error(f"RAG query error: {e}")
        return ""


def query_with_sources(question: str, k: int = 3) -> dict:
    """
    Same as query_regulations but also returns source document names.
    Useful for showing citations in the CAM report.
    """
    store = load_knowledge_base()
    if store is None:
        return {"context": "", "sources": []}

    try:
        docs = store.similarity_search_with_score(question, k=k)
        context_parts = []
        sources       = []

        for doc, score in docs:
            context_parts.append(doc.page_content)
            source = doc.metadata.get("source", "Unknown")
            page   = doc.metadata.get("page", "?")
            sources.append(f"{os.path.basename(source)} (page {page}) — relevance: {score:.2f}")

        return {
            "context": "\n\n".join(context_parts),
            "sources": sources,
        }
    except Exception as e:
        logger.error(f"RAG query_with_sources error: {e}")
        return {"context": "", "sources": []}


# ─────────────────────────────────────────────────────────────────────────────
# SAMPLE REGULATORY RULES  (used when no PDFs are loaded — for demo)
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_RBI_RULES = {
    "working_capital": (
        "RBI Circular: Working capital limits shall not exceed 25% of the assessed bank "
        "finance or INR 5 Crore, whichever is lower, for MSME borrowers. "
        "Banks must verify DSCR > 1.25 before sanction."
    ),
    "npa_classification": (
        "RBI NPA Norms: A credit facility is classified as Non-Performing Asset (NPA) "
        "when interest or principal amount remains overdue for more than 90 days. "
        "Sub-standard: NPA for up to 12 months. Doubtful: beyond 12 months."
    ),
    "gst_compliance": (
        "GST Circular 2024: GSTR-2A and GSTR-3B mismatch above 10% shall trigger "
        "a compliance notice. Banks must verify GST compliance before sanction of "
        "working capital loans above INR 5 Crore."
    ),
    "collateral": (
        "RBI Guidelines: For loans above INR 10 Crore, collateral coverage ratio "
        "must be minimum 1.25x of the sanctioned limit. Fixed assets must be "
        "independently valued within 3 years."
    ),
    "cibil": (
        "CIBIL Commercial Score: A score above 700 is considered creditworthy. "
        "Scores below 650 require additional security or co-guarantor. "
        "Credit bureaus include CIBIL, Equifax, Experian, and CRIF High Mark."
    ),
}


def get_sample_regulatory_context(topic: str) -> str:
    """Returns sample regulatory text for demo when no PDFs are loaded"""
    topic_lower = topic.lower()
    results = []
    for key, text in SAMPLE_RBI_RULES.items():
        if key in topic_lower or any(word in topic_lower for word in key.split("_")):
            results.append(text)
    return "\n\n".join(results) if results else list(SAMPLE_RBI_RULES.values())[0]
