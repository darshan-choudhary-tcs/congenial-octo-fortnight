"""
Example 2: Document Upload with RAG

This example demonstrates:
- Uploading a document
- Automatic metadata generation
- Querying the newly uploaded document
- Document management operations
"""

import requests
import json
from pathlib import Path
from typing import Dict, Any, List

# Configuration
BASE_URL = "http://localhost:8000"
USERNAME = "analyst@example.com"
PASSWORD = "password123"


def authenticate(username: str, password: str) -> str:
    """Authenticate and get JWT token."""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": username, "password": password}
    )
    response.raise_for_status()
    return response.json()["access_token"]


def upload_document(
    token: str,
    file_path: str,
    scope: str = "user",
    generate_metadata: bool = True
) -> Dict[str, Any]:
    """
    Upload a document to the system.

    Args:
        token: JWT access token
        file_path: Path to the file to upload
        scope: "user" for private, "global" for shared
        generate_metadata: Whether to auto-generate metadata with LLM

    Returns:
        Document metadata including ID, summary, keywords
    """
    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Prepare file
    file_path = Path(file_path)
    with open(file_path, "rb") as f:
        files = {
            "file": (file_path.name, f, "application/octet-stream")
        }

        data = {
            "scope": scope,
            "generate_metadata": str(generate_metadata).lower()
        }

        response = requests.post(
            f"{BASE_URL}/documents/upload",
            headers=headers,
            files=files,
            data=data
        )

    response.raise_for_status()
    return response.json()


def list_documents(
    token: str,
    scope: str = None,
    search: str = None
) -> List[Dict[str, Any]]:
    """
    List documents with optional filtering.

    Args:
        token: JWT access token
        scope: Filter by scope ("user" or "global")
        search: Search term for filename

    Returns:
        List of document metadata
    """
    headers = {
        "Authorization": f"Bearer {token}"
    }

    params = {}
    if scope:
        params["scope"] = scope
    if search:
        params["search"] = search

    response = requests.get(
        f"{BASE_URL}/documents",
        headers=headers,
        params=params
    )
    response.raise_for_status()
    return response.json()


def get_document(token: str, document_id: str) -> Dict[str, Any]:
    """Get detailed document information."""
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(
        f"{BASE_URL}/documents/{document_id}",
        headers=headers
    )
    response.raise_for_status()
    return response.json()


def regenerate_metadata(token: str, document_id: str) -> Dict[str, Any]:
    """Regenerate document metadata with LLM."""
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.post(
        f"{BASE_URL}/documents/{document_id}/regenerate-metadata",
        headers=headers
    )
    response.raise_for_status()
    return response.json()


def delete_document(token: str, document_id: str):
    """Delete a document."""
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.delete(
        f"{BASE_URL}/documents/{document_id}",
        headers=headers
    )
    response.raise_for_status()
    return response.json()


def query_document(token: str, document_id: str, query: str) -> Dict[str, Any]:
    """Query a specific document."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "message": query,
        "selected_documents": [document_id]
    }

    response = requests.post(
        f"{BASE_URL}/chat/message",
        headers=headers,
        json=payload
    )
    response.raise_for_status()
    return response.json()


def print_document_info(doc: Dict[str, Any]):
    """Pretty print document information."""
    print("\n" + "="*80)
    print("DOCUMENT INFORMATION")
    print("="*80)

    print(f"\nID: {doc['id']}")
    print(f"Filename: {doc['filename']}")
    print(f"File Type: {doc['file_type']}")
    print(f"File Size: {doc['file_size']:,} bytes")
    print(f"Scope: {doc['scope']}")
    print(f"Upload Date: {doc['upload_date']}")

    if doc.get('summary'):
        print(f"\n--- Summary ---")
        print(doc['summary'])

    if doc.get('keywords'):
        print(f"\n--- Keywords ---")
        print(", ".join(doc['keywords']))

    if doc.get('topics'):
        print(f"\n--- Topics ---")
        print(", ".join(doc['topics']))

    if doc.get('content_type'):
        print(f"\n--- Content Type ---")
        print(doc['content_type'])

    if doc.get('chunk_count'):
        print(f"\n--- Chunking Info ---")
        print(f"Total Chunks: {doc['chunk_count']}")

    print("="*80 + "\n")


def main():
    """Main example workflow."""
    print("=" * 80)
    print("DOCUMENT UPLOAD WITH RAG EXAMPLE")
    print("=" * 80)

    # Step 1: Authenticate
    print("\n[1/6] Authenticating...")
    try:
        token = authenticate(USERNAME, PASSWORD)
        print(f"✓ Successfully authenticated")
    except requests.exceptions.HTTPError as e:
        print(f"✗ Authentication failed: {e}")
        return

    # Step 2: Create a sample document
    print("\n[2/6] Creating sample document...")
    sample_file = Path("sample_ai_document.txt")
    sample_content = """
    Artificial Intelligence: An Overview

    Artificial Intelligence (AI) is the simulation of human intelligence processes
    by machines, especially computer systems. These processes include learning
    (the acquisition of information and rules for using the information), reasoning
    (using rules to reach approximate or definite conclusions), and self-correction.

    Key AI Technologies:
    1. Machine Learning (ML): Algorithms that improve through experience
    2. Natural Language Processing (NLP): Understanding and generating human language
    3. Computer Vision: Interpreting and understanding visual information
    4. Robotics: Physical AI systems that interact with the environment

    Applications of AI:
    - Healthcare: Disease diagnosis, drug discovery
    - Finance: Fraud detection, algorithmic trading
    - Transportation: Autonomous vehicles
    - Manufacturing: Quality control, predictive maintenance
    """

    sample_file.write_text(sample_content.strip())
    print(f"✓ Created sample file: {sample_file}")

    # Step 3: Upload document
    print("\n[3/6] Uploading document...")
    try:
        doc_response = upload_document(
            token,
            str(sample_file),
            scope="user",
            generate_metadata=True
        )
        print(f"✓ Document uploaded successfully")
        print_document_info(doc_response)

        document_id = doc_response['id']
    except requests.exceptions.HTTPError as e:
        print(f"✗ Upload failed: {e}")
        sample_file.unlink()
        return

    # Step 4: List documents
    print("\n[4/6] Listing all documents...")
    try:
        docs = list_documents(token, scope="user")
        print(f"✓ Found {len(docs)} user documents")
        for i, doc in enumerate(docs[:3], 1):
            print(f"  {i}. {doc['filename']} ({doc['file_type']})")
    except requests.exceptions.HTTPError as e:
        print(f"✗ Failed to list documents: {e}")

    # Step 5: Query the uploaded document
    print("\n[5/6] Querying the uploaded document...")
    query = "What are the key AI technologies mentioned in this document?"

    try:
        response = query_document(token, document_id, query)
        print(f"✓ Query executed successfully")
        print(f"\n--- Query ---")
        print(query)
        print(f"\n--- Answer ---")
        print(response['message']['content'])
        print(f"\nConfidence: {response['confidence_score']:.2%}")
    except requests.exceptions.HTTPError as e:
        print(f"✗ Query failed: {e}")

    # Step 6: Cleanup
    print("\n[6/6] Cleaning up...")
    try:
        delete_document(token, document_id)
        print(f"✓ Document deleted from system")
    except requests.exceptions.HTTPError as e:
        print(f"✗ Failed to delete document: {e}")

    # Delete local file
    sample_file.unlink()
    print(f"✓ Local file deleted")

    print("\n✓ Example completed successfully!")


if __name__ == "__main__":
    main()


"""
EXPECTED OUTPUT:
================================================================================
DOCUMENT UPLOAD WITH RAG EXAMPLE
================================================================================

[1/6] Authenticating...
✓ Successfully authenticated

[2/6] Creating sample document...
✓ Created sample file: sample_ai_document.txt

[3/6] Uploading document...
✓ Document uploaded successfully

================================================================================
DOCUMENT INFORMATION
================================================================================

ID: 550e8400-e29b-41d4-a716-446655440000
Filename: sample_ai_document.txt
File Type: txt
File Size: 1,234 bytes
Scope: user
Upload Date: 2025-01-15T10:30:00

--- Summary ---
This document provides an overview of Artificial Intelligence, covering key
technologies like Machine Learning, Natural Language Processing, and Computer
Vision, along with various real-world applications across industries.

--- Keywords ---
artificial intelligence, machine learning, NLP, computer vision, robotics,
healthcare, finance, autonomous vehicles

--- Topics ---
AI Technologies, Machine Learning, Applications of AI, Industry Use Cases

--- Content Type ---
Technical Overview

--- Chunking Info ---
Total Chunks: 3

================================================================================

[4/6] Listing all documents...
✓ Found 5 user documents
  1. sample_ai_document.txt (txt)
  2. ml_fundamentals.pdf (pdf)
  3. data_analysis.csv (csv)

[5/6] Querying the uploaded document...
✓ Query executed successfully

--- Query ---
What are the key AI technologies mentioned in this document?

--- Answer ---
According to the document, the key AI technologies are:

1. Machine Learning (ML) - Algorithms that improve through experience [Source 1]
2. Natural Language Processing (NLP) - Understanding and generating human language [Source 1]
3. Computer Vision - Interpreting and understanding visual information [Source 1]
4. Robotics - Physical AI systems that interact with the environment [Source 1]

These technologies form the foundation of modern artificial intelligence systems.

Confidence: 92.34%

[6/6] Cleaning up...
✓ Document deleted from system
✓ Local file deleted

✓ Example completed successfully!
"""
