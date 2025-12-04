"""
Example 1: Basic Chat Workflow

This example demonstrates:
- User authentication
- Sending a chat message
- Receiving a response with RAG context
- Viewing source documents
"""

import requests
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
USERNAME = "analyst@example.com"
PASSWORD = "password123"


def authenticate(username: str, password: str) -> str:
    """
    Authenticate and get JWT token.

    Returns:
        JWT access token
    """
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": username,
            "password": password
        }
    )
    response.raise_for_status()
    return response.json()["access_token"]


def send_message(token: str, message: str, conversation_id: str = None) -> Dict[str, Any]:
    """
    Send a message to the chat API.

    Args:
        token: JWT access token
        message: User's message
        conversation_id: Optional conversation ID for context

    Returns:
        Response data with AI message and RAG context
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "message": message
    }

    if conversation_id:
        payload["conversation_id"] = conversation_id

    response = requests.post(
        f"{BASE_URL}/chat/message",
        headers=headers,
        json=payload
    )
    response.raise_for_status()
    return response.json()


def print_response(response: Dict[str, Any]):
    """Pretty print the chat response."""
    print("\n" + "="*80)
    print("CHAT RESPONSE")
    print("="*80)

    # Basic info
    print(f"\nConversation ID: {response['conversation_id']}")
    print(f"Message ID: {response['message']['id']}")
    print(f"Confidence Score: {response['confidence_score']:.2%}")

    # AI Response
    print(f"\n--- AI Response ---")
    print(response['message']['content'])

    # Source documents
    if response.get('documents_used'):
        print(f"\n--- Source Documents ({len(response['documents_used'])}) ---")
        for i, doc in enumerate(response['documents_used'], 1):
            print(f"{i}. {doc['filename']}")
            print(f"   Relevance: {doc['relevance_score']:.2%}")
            if doc.get('summary'):
                print(f"   Summary: {doc['summary'][:100]}...")

    # Metadata
    print(f"\n--- Metadata ---")
    print(f"Tokens Used: {response['token_count']}")
    print(f"LLM Provider: {response['llm_provider']}")
    print(f"Low Confidence Warning: {response['low_confidence_warning']}")

    print("="*80 + "\n")


def main():
    """Main example workflow."""
    print("=" * 80)
    print("BASIC CHAT WORKFLOW EXAMPLE")
    print("=" * 80)

    # Step 1: Authenticate
    print("\n[1/3] Authenticating...")
    try:
        token = authenticate(USERNAME, PASSWORD)
        print(f"✓ Successfully authenticated")
    except requests.exceptions.HTTPError as e:
        print(f"✗ Authentication failed: {e}")
        return

    # Step 2: Send first message (creates new conversation)
    print("\n[2/3] Sending first message...")
    first_message = "What are the main topics covered in the uploaded documents?"

    try:
        response1 = send_message(token, first_message)
        print(f"✓ Message sent successfully")
        print_response(response1)

        conversation_id = response1['conversation_id']
    except requests.exceptions.HTTPError as e:
        print(f"✗ Failed to send message: {e}")
        return

    # Step 3: Send follow-up message (continues conversation)
    print("\n[3/3] Sending follow-up message...")
    follow_up_message = "Can you provide more details about the first topic?"

    try:
        response2 = send_message(token, follow_up_message, conversation_id)
        print(f"✓ Follow-up sent successfully")
        print_response(response2)
    except requests.exceptions.HTTPError as e:
        print(f"✗ Failed to send follow-up: {e}")
        return

    print("\n✓ Example completed successfully!")


if __name__ == "__main__":
    main()


"""
EXPECTED OUTPUT:
================================================================================
BASIC CHAT WORKFLOW EXAMPLE
================================================================================

[1/3] Authenticating...
✓ Successfully authenticated

[2/3] Sending first message...
✓ Message sent successfully

================================================================================
CHAT RESPONSE
================================================================================

Conversation ID: 550e8400-e29b-41d4-a716-446655440000
Message ID: 550e8400-e29b-41d4-a716-446655440001
Confidence Score: 85.34%

--- AI Response ---
Based on the uploaded documents, the main topics covered are:

1. Machine Learning Fundamentals [Source 1]
2. Natural Language Processing [Source 2]
3. Computer Vision Applications [Source 3]

The documents provide comprehensive coverage of these AI domains...

--- Source Documents (3) ---
1. ML_Fundamentals.pdf
   Relevance: 92.45%
   Summary: This document covers the basic concepts of machine learning...
2. NLP_Guide.pdf
   Relevance: 88.12%
   Summary: A comprehensive guide to natural language processing...
3. CV_Applications.pdf
   Relevance: 76.89%
   Summary: Overview of computer vision applications in industry...

--- Metadata ---
Tokens Used: 1234
LLM Provider: custom_api
Low Confidence Warning: False

================================================================================

[3/3] Sending follow-up message...
✓ Follow-up sent successfully

================================================================================
CHAT RESPONSE
================================================================================
...

✓ Example completed successfully!
"""
