"""
Example 4: Multi-Agent Orchestration and Monitoring

This example demonstrates:
- Agent execution lifecycle
- Agent logs and monitoring
- Grounding verification process
- Explainability features
"""

import requests
import json
from typing import Dict, Any, List
from datetime import datetime

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


def send_message_with_agents(token: str, message: str) -> Dict[str, Any]:
    """Send a message that triggers multi-agent execution."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "message": message,
        "enable_grounding": True,  # Enable grounding verification
        "explainability_level": "detailed"  # Get detailed explanations
    }

    response = requests.post(
        f"{BASE_URL}/chat/message",
        headers=headers,
        json=payload
    )
    response.raise_for_status()
    return response.json()


def get_agent_status(token: str) -> Dict[str, Any]:
    """Get current agent execution status."""
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(
        f"{BASE_URL}/agents/status",
        headers=headers
    )
    response.raise_for_status()
    return response.json()


def get_agent_logs(
    token: str,
    agent_type: str = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Get agent execution logs.

    Args:
        token: JWT access token
        agent_type: Filter by agent type (research, analyzer, grounding, explainability)
        limit: Maximum number of logs to return

    Returns:
        List of agent logs
    """
    headers = {
        "Authorization": f"Bearer {token}"
    }

    params = {"limit": limit}
    if agent_type:
        params["agent_type"] = agent_type

    response = requests.get(
        f"{BASE_URL}/agents/logs",
        headers=headers,
        params=params
    )
    response.raise_for_status()
    return response.json()


def get_message_agent_logs(token: str, message_id: str) -> List[Dict[str, Any]]:
    """Get all agent logs for a specific message."""
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(
        f"{BASE_URL}/agents/logs/message/{message_id}",
        headers=headers
    )
    response.raise_for_status()
    return response.json()


def get_explainability_data(token: str, message_id: str) -> Dict[str, Any]:
    """Get explainability data for a message."""
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(
        f"{BASE_URL}/explainability/message/{message_id}",
        headers=headers
    )
    response.raise_for_status()
    return response.json()


def print_agent_logs(logs: List[Dict[str, Any]]):
    """Pretty print agent logs."""
    print("\n" + "="*80)
    print("AGENT EXECUTION LOGS")
    print("="*80)

    for i, log in enumerate(logs, 1):
        print(f"\n[{i}] {log['agent_type'].upper()} AGENT")
        print(f"    Status: {log['status']}")
        print(f"    Started: {log['start_time']}")
        print(f"    Ended: {log['end_time']}")
        print(f"    Duration: {log.get('duration_ms', 0)/1000:.2f}s")

        if log.get('input_data'):
            print(f"    Input: {log['input_data'][:100]}...")

        if log.get('output_data'):
            print(f"    Output: {log['output_data'][:100]}...")

        if log.get('metadata'):
            print(f"    Metadata: {json.dumps(log['metadata'], indent=6)}")

        if log.get('error_message'):
            print(f"    ❌ Error: {log['error_message']}")

    print("="*80 + "\n")


def print_explainability_data(data: Dict[str, Any]):
    """Pretty print explainability data."""
    print("\n" + "="*80)
    print("EXPLAINABILITY ANALYSIS")
    print("="*80)

    print(f"\nMessage ID: {data['message_id']}")
    print(f"Level: {data['explainability_level']}")

    # Confidence breakdown
    print(f"\n--- Confidence Breakdown ---")
    confidence = data.get('confidence_breakdown', {})
    print(f"Overall Score: {confidence.get('overall_score', 0):.2%}")
    print(f"  • Similarity: {confidence.get('similarity_score', 0):.2%}")
    print(f"  • Citations: {confidence.get('citation_score', 0):.2%}")
    print(f"  • Query Quality: {confidence.get('query_quality_score', 0):.2%}")
    print(f"  • Response Length: {confidence.get('response_length_score', 0):.2%}")

    # Reasoning chain
    if data.get('reasoning_chain'):
        print(f"\n--- Reasoning Chain ---")
        for i, step in enumerate(data['reasoning_chain'], 1):
            print(f"{i}. {step['step']}: {step['description']}")
            if step.get('confidence'):
                print(f"   Confidence: {step['confidence']:.2%}")

    # Grounding verification
    if data.get('grounding_verification'):
        print(f"\n--- Grounding Verification ---")
        grounding = data['grounding_verification']
        print(f"Status: {grounding['status']}")
        print(f"Score: {grounding['score']:.2%}")

        if grounding.get('claims_verified'):
            print(f"\nClaims Verified: {len(grounding['claims_verified'])}")
            for i, claim in enumerate(grounding['claims_verified'][:3], 1):
                print(f"  {i}. {claim['claim']}")
                print(f"     Verified: {'✓' if claim['verified'] else '✗'}")
                print(f"     Confidence: {claim['confidence']:.2%}")

    # Retrieved documents
    if data.get('retrieved_documents'):
        print(f"\n--- Retrieved Documents ---")
        for i, doc in enumerate(data['retrieved_documents'], 1):
            print(f"{i}. {doc['filename']}")
            print(f"   Relevance: {doc['relevance_score']:.2%}")
            print(f"   Chunks Used: {doc['chunks_used']}")

    print("="*80 + "\n")


def main():
    """Main example workflow."""
    print("=" * 80)
    print("MULTI-AGENT ORCHESTRATION EXAMPLE")
    print("=" * 80)

    # Step 1: Authenticate
    print("\n[1/5] Authenticating...")
    try:
        token = authenticate(USERNAME, PASSWORD)
        print(f"✓ Successfully authenticated")
    except requests.exceptions.HTTPError as e:
        print(f"✗ Authentication failed: {e}")
        return

    # Step 2: Check agent status
    print("\n[2/5] Checking agent status...")
    try:
        status = get_agent_status(token)
        print(f"✓ Agent system status: {status.get('status', 'unknown')}")
        print(f"  Available Agents: {', '.join(status.get('available_agents', []))}")
    except requests.exceptions.HTTPError as e:
        print(f"✗ Failed to get agent status: {e}")

    # Step 3: Send message with agent orchestration
    print("\n[3/5] Sending message with multi-agent processing...")
    message = "What are the main applications of machine learning in healthcare?"
    print(f"Query: {message}")

    try:
        response = send_message_with_agents(token, message)
        print(f"✓ Message processed successfully")
        print(f"\n--- AI Response ---")
        print(response['message']['content'])
        print(f"\nConfidence: {response['confidence_score']:.2%}")
        print(f"Documents Used: {len(response.get('documents_used', []))}")
        print(f"Grounding Status: {response.get('grounding_status', 'N/A')}")

        message_id = response['message']['id']
    except requests.exceptions.HTTPError as e:
        print(f"✗ Failed to send message: {e}")
        return

    # Step 4: Get agent logs for this message
    print("\n[4/5] Retrieving agent execution logs...")
    try:
        logs = get_message_agent_logs(token, message_id)
        print(f"✓ Retrieved {len(logs)} agent logs")
        print_agent_logs(logs)
    except requests.exceptions.HTTPError as e:
        print(f"✗ Failed to get agent logs: {e}")

    # Step 5: Get detailed explainability data
    print("\n[5/5] Retrieving explainability data...")
    try:
        explainability = get_explainability_data(token, message_id)
        print(f"✓ Retrieved explainability data")
        print_explainability_data(explainability)
    except requests.exceptions.HTTPError as e:
        print(f"✗ Failed to get explainability data: {e}")

    # Bonus: Get recent agent logs across all messages
    print("\n[Bonus] Recent agent activity...")
    try:
        recent_logs = get_agent_logs(token, limit=5)
        print(f"✓ Last 5 agent executions:")
        for i, log in enumerate(recent_logs, 1):
            print(f"  {i}. {log['agent_type']} - {log['status']} - "
                  f"{log.get('duration_ms', 0)/1000:.2f}s")
    except requests.exceptions.HTTPError as e:
        print(f"✗ Failed to get recent logs: {e}")

    print("\n✓ Example completed successfully!")


if __name__ == "__main__":
    main()


"""
EXPECTED OUTPUT:
================================================================================
MULTI-AGENT ORCHESTRATION EXAMPLE
================================================================================

[1/5] Authenticating...
✓ Successfully authenticated

[2/5] Checking agent status...
✓ Agent system status: operational
  Available Agents: research, analyzer, grounding, explainability

[3/5] Sending message with multi-agent processing...
Query: What are the main applications of machine learning in healthcare?
✓ Message processed successfully

--- AI Response ---
Machine learning has numerous applications in healthcare, including:

1. **Disease Diagnosis**: ML algorithms analyze medical images (X-rays, MRIs) to
   detect diseases like cancer with high accuracy [Source 1]

2. **Drug Discovery**: ML accelerates the identification of potential drug
   candidates by predicting molecular behavior [Source 2]

3. **Predictive Analytics**: ML models predict patient outcomes, readmission risks,
   and disease progression [Source 3]

4. **Personalized Treatment**: ML analyzes patient data to recommend tailored
   treatment plans based on individual characteristics [Source 1]

5. **Medical Imaging**: Computer vision algorithms assist radiologists in
   detecting abnormalities [Source 2]

Confidence: 89.23%
Documents Used: 3
Grounding Status: verified

[4/5] Retrieving agent execution logs...
✓ Retrieved 4 agent logs

================================================================================
AGENT EXECUTION LOGS
================================================================================

[1] RESEARCH AGENT
    Status: completed
    Started: 2025-01-15T10:30:00
    Ended: 2025-01-15T10:30:02
    Duration: 2.14s
    Input: What are the main applications of machine learning in healthcare?
    Output: Retrieved 15 relevant document chunks from 3 documents
    Metadata: {
      "documents_retrieved": 3,
      "chunks_retrieved": 15,
      "avg_relevance": 0.87
    }

[2] ANALYZER AGENT
    Status: completed
    Started: 2025-01-15T10:30:02
    Ended: 2025-01-15T10:30:04
    Duration: 1.89s
    Input: Analysis request for healthcare ML applications
    Output: Generated comprehensive response with 5 key applications
    Metadata: {
      "response_length": 456,
      "citations_added": 3,
      "topics_covered": 5
    }

[3] GROUNDING AGENT
    Status: completed
    Started: 2025-01-15T10:30:04
    Ended: 2025-01-15T10:30:05
    Duration: 1.12s
    Input: Verify response claims against source documents
    Output: All claims verified successfully
    Metadata: {
      "claims_extracted": 7,
      "claims_verified": 7,
      "verification_rate": 1.0
    }

[4] EXPLAINABILITY AGENT
    Status: completed
    Started: 2025-01-15T10:30:05
    Ended: 2025-01-15T10:30:06
    Duration: 0.87s
    Input: Generate explainability data
    Output: Created detailed reasoning chain and confidence breakdown
    Metadata: {
      "confidence_factors": 4,
      "reasoning_steps": 6
    }

================================================================================

[5/5] Retrieving explainability data...
✓ Retrieved explainability data

================================================================================
EXPLAINABILITY ANALYSIS
================================================================================

Message ID: 550e8400-e29b-41d4-a716-446655440001
Level: detailed

--- Confidence Breakdown ---
Overall Score: 89.23%
  • Similarity: 87.45%
  • Citations: 93.33%
  • Query Quality: 90.00%
  • Response Length: 85.00%

--- Reasoning Chain ---
1. query_analysis: Analyzed query intent - healthcare ML applications
   Confidence: 95.00%
2. document_retrieval: Retrieved 15 relevant chunks from 3 documents
   Confidence: 87.45%
3. response_generation: Generated comprehensive answer with 5 applications
   Confidence: 88.00%
4. citation_addition: Added [Source N] citations for all claims
   Confidence: 93.33%
5. grounding_verification: Verified all claims against source documents
   Confidence: 100.00%
6. quality_assessment: Final response quality check passed
   Confidence: 89.23%

--- Grounding Verification ---
Status: verified
Score: 95.71%

Claims Verified: 7
  1. ML algorithms analyze medical images for disease detection
     Verified: ✓
     Confidence: 97.00%
  2. ML accelerates drug discovery by predicting molecular behavior
     Verified: ✓
     Confidence: 94.00%
  3. ML models predict patient outcomes and readmission risks
     Verified: ✓
     Confidence: 96.00%

--- Retrieved Documents ---
1. healthcare_ml_applications.pdf
   Relevance: 92.34%
   Chunks Used: 6
2. medical_ai_overview.txt
   Relevance: 88.12%
   Chunks Used: 5
3. clinical_ml_systems.pdf
   Relevance: 81.76%
   Chunks Used: 4

================================================================================

[Bonus] Recent agent activity...
✓ Last 5 agent executions:
  1. explainability - completed - 0.87s
  2. grounding - completed - 1.12s
  3. analyzer - completed - 1.89s
  4. research - completed - 2.14s
  5. research - completed - 1.56s

✓ Example completed successfully!
"""
