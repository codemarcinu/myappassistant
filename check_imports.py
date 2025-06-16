print("Checking imports...")
try:
    import numpy as np
    print("✅ numpy is available")
except ImportError as e:
    print(f"❌ numpy error: {e}")

try:
    import faiss
    print("✅ faiss is available")
except ImportError as e:
    print(f"❌ faiss error: {e}")

try:
    import pytz
    print("✅ pytz is available")
except ImportError as e:
    print(f"❌ pytz error: {e}")

try:
    from sqlalchemy.ext.asyncio import AsyncSession
    print("✅ sqlalchemy.ext.asyncio is available")
except ImportError as e:
    print(f"❌ sqlalchemy.ext.asyncio error: {e}")

try:
    from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader, DirectoryLoader
    from langchain_community.document_loaders.word_document import UnstructuredWordDocumentLoader
    from langchain_community.document_loaders.email import UnstructuredEmailLoader
    from langchain_community.document_loaders.powerpoint import UnstructuredPowerPointLoader
    from langchain_community.document_loaders.markdown import UnstructuredMarkdownLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    print("✅ langchain modules are available")
except ImportError as e:
    print(f"❌ langchain error: {e}")

try:
    import pinecone
    print("✅ pinecone is available")
except ImportError as e:
    print(f"❌ pinecone error: {e}")

try:
    from sentence_transformers import SentenceTransformer
    print("✅ sentence_transformers is available")
except ImportError as e:
    print(f"❌ sentence_transformers error: {e}")

print("Import checks completed.")