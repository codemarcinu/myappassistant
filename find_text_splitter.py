import importlib
import pkgutil

# Check all possible locations for RecursiveCharacterTextSplitter
possible_locations = [
    "langchain.text_splitter",
    "langchain_community.text_splitter",
    "langchain.text_splitters",
    "langchain_community.text_splitters",
    "langchain.schema.text_splitter",
    "langchain_community.schema.text_splitter",
    "langchain_core.text_splitter",
    "langchain_core.text_splitters"
]

for location in possible_locations:
    try:
        module = importlib.import_module(location)
        print(f"✅ Module {location} exists")
        
        # Check if RecursiveCharacterTextSplitter is in this module
        try:
            if hasattr(module, "RecursiveCharacterTextSplitter"):
                print(f"✅ RecursiveCharacterTextSplitter found in {location}")
            else:
                print(f"❌ RecursiveCharacterTextSplitter not found in {location}")
                
                # List all attributes in the module
                print(f"Available classes in {location}:")
                for attr in dir(module):
                    if not attr.startswith("_"):  # Skip private attributes
                        print(f"  - {attr}")
        except Exception as e:
            print(f"Error checking for RecursiveCharacterTextSplitter: {e}")
            
    except ImportError:
        print(f"❌ Module {location} does not exist")

print("\nDone searching for RecursiveCharacterTextSplitter.")