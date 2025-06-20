print("Checking imports...")
try:
    import numpy as np  # noqa: F401

    print("✅ numpy is available (unused in this script)")
except ImportError as e:
    print(f"❌ numpy error: {e}")

try:
    import faiss  # noqa: F401

    print("✅ faiss is available (unused in this script)")
except ImportError as e:
    print(f"❌ faiss error: {e}")

try:
    import pytz  # noqa: F401

    print("✅ pytz is available (unused in this script)")
except ImportError as e:
    print(f"❌ pytz error: {e}")

try:
    from sqlalchemy.ext.asyncio import AsyncSession  # noqa: F401

    print("✅ sqlalchemy.ext.asyncio is available (unused in this script)")
except ImportError as e:
    print(f"❌ sqlalchemy.ext.asyncio error: {e}")

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter  # noqa: F401
    from langchain_community.document_loaders import (  # noqa: F401
        DirectoryLoader,
        PyPDFLoader,
        WebBaseLoader,
    )

    print("✅ langchain modules are available (unused in this script)")
except ImportError as e:
    print(f"❌ langchain error: {e}")

try:
    import pinecone  # noqa: F401

    print("✅ pinecone is available (unused in this script)")
except ImportError as e:
    print(f"❌ pinecone error: {e}")

try:
    from sentence_transformers import SentenceTransformer  # noqa: F401

    print("✅ sentence_transformers is available (unused in this script)")
except ImportError as e:
    print(f"❌ sentence_transformers error: {e}")

print("Import checks completed.")
