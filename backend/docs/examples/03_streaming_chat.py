"""
Example 3: Streaming Chat with Real-Time Updates

This example demonstrates:
- Server-Sent Events (SSE) for streaming
- Real-time token delivery
- Agent execution progress tracking
- Handling streaming responses
"""

import requests
import json
import time
from typing import Iterator, Dict, Any

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


def stream_chat(
    token: str,
    message: str,
    conversation_id: str = None
) -> Iterator[Dict[str, Any]]:
    """
    Send a message and stream the response.

    Args:
        token: JWT access token
        message: User's message
        conversation_id: Optional conversation ID

    Yields:
        Server-sent events as dictionaries
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }

    payload = {
        "message": message
    }

    if conversation_id:
        payload["conversation_id"] = conversation_id

    response = requests.post(
        f"{BASE_URL}/chat/stream",
        headers=headers,
        json=payload,
        stream=True
    )
    response.raise_for_status()

    # Parse SSE stream
    for line in response.iter_lines():
        if not line:
            continue

        line = line.decode('utf-8')

        # SSE format: "data: {json}"
        if line.startswith('data: '):
            data = line[6:]  # Remove "data: " prefix

            if data == '[DONE]':
                break

            try:
                yield json.loads(data)
            except json.JSONDecodeError:
                continue


def handle_stream_event(event: Dict[str, Any]):
    """
    Process and display a streaming event.

    Event types:
    - agent_start: Agent begins execution
    - agent_end: Agent completes execution
    - token: New token in response
    - metadata: Additional metadata
    - complete: Stream finished
    """
    event_type = event.get('type')

    if event_type == 'agent_start':
        print(f"\n🤖 Agent: {event['agent_name']} starting...", flush=True)

    elif event_type == 'agent_end':
        print(f"✓ Agent: {event['agent_name']} completed", flush=True)

    elif event_type == 'token':
        # Print token without newline for streaming effect
        print(event['content'], end='', flush=True)

    elif event_type == 'metadata':
        # Store metadata for later display
        return event.get('data')

    elif event_type == 'complete':
        print("\n")  # New line after complete response
        return event

    elif event_type == 'error':
        print(f"\n❌ Error: {event.get('message')}", flush=True)


def main():
    """Main example workflow."""
    print("=" * 80)
    print("STREAMING CHAT EXAMPLE")
    print("=" * 80)

    # Step 1: Authenticate
    print("\n[1/3] Authenticating...")
    try:
        token = authenticate(USERNAME, PASSWORD)
        print(f"✓ Successfully authenticated\n")
    except requests.exceptions.HTTPError as e:
        print(f"✗ Authentication failed: {e}")
        return

    # Step 2: Send message with streaming
    print("[2/3] Sending message with streaming enabled...")
    message = "Explain the concept of machine learning in detail."
    print(f"\n📝 User: {message}\n")

    start_time = time.time()
    metadata = None

    try:
        print("🤖 AI: ", end='', flush=True)

        for event in stream_chat(token, message):
            result = handle_stream_event(event)

            if result and event.get('type') == 'complete':
                metadata = result

        end_time = time.time()

        # Display metadata
        if metadata:
            print("\n" + "-" * 80)
            print("METADATA")
            print("-" * 80)
            print(f"Conversation ID: {metadata.get('conversation_id')}")
            print(f"Message ID: {metadata.get('message_id')}")
            print(f"Confidence Score: {metadata.get('confidence_score', 0):.2%}")
            print(f"Tokens Used: {metadata.get('token_count', 0)}")
            print(f"LLM Provider: {metadata.get('llm_provider', 'N/A')}")
            print(f"Time Taken: {end_time - start_time:.2f}s")

            if metadata.get('documents_used'):
                print(f"\nSource Documents: {len(metadata['documents_used'])}")
                for i, doc in enumerate(metadata['documents_used'][:3], 1):
                    print(f"  {i}. {doc['filename']} ({doc['relevance_score']:.2%})")

            print("-" * 80)

            conversation_id = metadata.get('conversation_id')

    except requests.exceptions.HTTPError as e:
        print(f"\n✗ Streaming failed: {e}")
        return
    except KeyboardInterrupt:
        print(f"\n\n⚠ Stream interrupted by user")
        return

    # Step 3: Send follow-up with streaming
    print("\n[3/3] Sending follow-up message...")
    follow_up = "Can you give a simple example?"
    print(f"\n📝 User: {follow_up}\n")

    try:
        print("🤖 AI: ", end='', flush=True)

        for event in stream_chat(token, follow_up, conversation_id):
            result = handle_stream_event(event)

            if result and event.get('type') == 'complete':
                metadata = result

        # Display metadata
        if metadata:
            print(f"\nConfidence: {metadata.get('confidence_score', 0):.2%} | "
                  f"Tokens: {metadata.get('token_count', 0)}")

    except requests.exceptions.HTTPError as e:
        print(f"\n✗ Streaming failed: {e}")
        return

    print("\n✓ Example completed successfully!")


if __name__ == "__main__":
    main()


"""
EXPECTED OUTPUT:
================================================================================
STREAMING CHAT EXAMPLE
================================================================================

[1/3] Authenticating...
✓ Successfully authenticated

[2/3] Sending message with streaming enabled...

📝 User: Explain the concept of machine learning in detail.

🤖 Agent: ResearchAgent starting...
✓ Agent: ResearchAgent completed

🤖 AI: Machine learning is a subset of artificial intelligence that enables
systems to learn and improve from experience without being explicitly programmed.
Here's a detailed explanation:

**Core Concept**
Machine learning algorithms use statistical techniques to enable computers to
"learn" from data. The system identifies patterns in the data and uses these
patterns to make predictions or decisions. [Source 1]

**Types of Machine Learning**

1. **Supervised Learning**: The algorithm learns from labeled training data
   - Examples: Image classification, spam detection
   - Requires human-labeled examples

2. **Unsupervised Learning**: The algorithm finds patterns in unlabeled data
   - Examples: Customer segmentation, anomaly detection
   - No predefined labels needed [Source 2]

3. **Reinforcement Learning**: The algorithm learns through trial and error
   - Examples: Game playing, robotics
   - Uses rewards and penalties

**Key Components**
- Training Data: Historical examples for learning
- Features: Input variables the model uses
- Model: Mathematical representation of patterns
- Predictions: Output based on learned patterns [Source 3]

Machine learning powers many modern applications including recommendation
systems, voice assistants, and autonomous vehicles.

--------------------------------------------------------------------------------
METADATA
--------------------------------------------------------------------------------
Conversation ID: 550e8400-e29b-41d4-a716-446655440000
Message ID: 550e8400-e29b-41d4-a716-446655440001
Confidence Score: 88.45%
Tokens Used: 342
LLM Provider: custom_api
Time Taken: 3.24s

Source Documents: 3
  1. ML_Fundamentals.pdf (94.23%)
  2. AI_Overview.txt (87.65%)
  3. Data_Science_Handbook.pdf (76.12%)
--------------------------------------------------------------------------------

[3/3] Sending follow-up message...

📝 User: Can you give a simple example?

🤖 Agent: ResearchAgent starting...
✓ Agent: ResearchAgent completed

🤖 AI: Here's a simple example of supervised machine learning:

**Email Spam Detection**

Training Phase:
1. Collect 1000 emails (500 spam, 500 not spam)
2. Label each email as "spam" or "not spam"
3. Extract features: word frequency, sender info, links
4. Train the model to recognize patterns

Example features:
- Contains "free money": High spam indicator
- From known contact: Low spam indicator
- Many links: High spam indicator

Prediction Phase:
When a new email arrives:
1. Extract the same features
2. The model analyzes these features
3. Predicts: "spam" (95% confidence) or "not spam" (5% confidence)
4. System moves email to spam folder if confidence > 50%

The model learned the patterns from training data and now applies them to new,
unseen emails. [Source 1]

Confidence: 91.23% | Tokens: 187

✓ Example completed successfully!
"""


"""
ADVANCED USAGE: Custom Stream Handler

You can create a custom handler for more control:
"""

class ChatStreamHandler:
    """Custom handler for streaming chat responses."""

    def __init__(self):
        self.full_response = ""
        self.metadata = {}
        self.agents_executed = []

    def handle_event(self, event: Dict[str, Any]):
        """Process each streaming event."""
        event_type = event.get('type')

        if event_type == 'agent_start':
            self.agents_executed.append(event['agent_name'])
            print(f"\n[Agent: {event['agent_name']}] Starting...", flush=True)

        elif event_type == 'agent_end':
            print(f"[Agent: {event['agent_name']}] Done", flush=True)

        elif event_type == 'token':
            token = event['content']
            self.full_response += token
            print(token, end='', flush=True)

        elif event_type == 'metadata':
            self.metadata = event.get('data', {})

        elif event_type == 'complete':
            print("\n")
            return True  # Signal completion

        return False

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of the streaming session."""
        return {
            'full_response': self.full_response,
            'metadata': self.metadata,
            'agents_executed': self.agents_executed,
            'response_length': len(self.full_response),
            'word_count': len(self.full_response.split())
        }


# Usage:
# handler = ChatStreamHandler()
# for event in stream_chat(token, message):
#     if handler.handle_event(event):
#         break
# summary = handler.get_summary()
