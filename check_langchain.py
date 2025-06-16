import importlib
import pkgutil

# Check what's available in langchain_community
print("Checking langchain_community package structure...")
try:
    import langchain_community
    print("✅ langchain_community is installed")
    
    # Check if document_loaders exists
    try:
        import langchain_community.document_loaders
        print("✅ langchain_community.document_loaders module exists")
        
        # List all available modules in document_loaders
        print("\nAvailable modules in langchain_community.document_loaders:")
        for importer, modname, ispkg in pkgutil.iter_modules(langchain_community.document_loaders.__path__):
            print(f"- {modname}")
            
        # Try direct imports of common loaders
        print("\nTrying direct imports:")
        loaders = [
            "PyPDFLoader", 
            "PDFMinerLoader",
            "UnstructuredPDFLoader",
            "PyPDFDirectoryLoader",
            "DirectoryLoader"
        ]
        
        for loader in loaders:
            try:
                exec(f"from langchain_community.document_loaders import {loader}")
                print(f"✅ Successfully imported {loader}")
            except ImportError as e:
                print(f"❌ Could not import {loader}: {e}")
                
    except ImportError as e:
        print(f"❌ langchain_community.document_loaders error: {e}")
    
except ImportError as e:
    print(f"❌ langchain_community error: {e}")

print("\nDone checking langchain_community.")