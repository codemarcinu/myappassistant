import os
from typing import List


def load_documents(directory: str) -> List[str]:
    """
    Loads all text files from a directory.
    """
    documents = []
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            with open(os.path.join(directory, filename), "r") as f:
                documents.append(f.read())
    return documents
