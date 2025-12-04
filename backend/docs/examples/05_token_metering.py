"""
Example 5: Token Usage Metering and Cost Analysis

This example demonstrates:
- Tracking token usage across different operations
- Cost estimation for LLM calls
- Usage analytics by user, conversation, and agent
- Cost optimization strategies
"""

import requests
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_USERNAME = "admin@example.com"
ADMIN_PASSWORD = "admin123"

# Cost per 1M tokens (example pricing)
PRICING = {
    "custom_api": {
        "input": 0.27,  # $0.27 per 1M input tokens (DeepSeek-V3)
        "output": 1.10   # $1.10 per 1M output tokens
    },
    "ollama": {
        "input": 0.0,   # Free (local)
        "output": 0.0
    }
}


def authenticate(username: str, password: str) -> str:
    """Authenticate and get JWT token."""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": username, "password": password}
    )
    response.raise_for_status()
    return response.json()["access_token"]


def get_user_usage(
    token: str,
    user_id: str,
    start_date: str = None,
    end_date: str = None
) -> Dict[str, Any]:
    """
    Get token usage for a specific user.

    Args:
        token: JWT access token (admin required)
        user_id: User ID
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        Usage statistics
    """
    headers = {
        "Authorization": f"Bearer {token}"
    }

    params = {}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date

    response = requests.get(
        f"{BASE_URL}/metering/user/{user_id}/usage",
        headers=headers,
        params=params
    )
    response.raise_for_status()
    return response.json()


def get_overall_usage(token: str) -> Dict[str, Any]:
    """Get system-wide token usage (admin only)."""
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(
        f"{BASE_URL}/metering/overall",
        headers=headers
    )
    response.raise_for_status()
    return response.json()


def get_conversation_usage(token: str, conversation_id: str) -> Dict[str, Any]:
    """Get token usage for a specific conversation."""
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(
        f"{BASE_URL}/metering/conversation/{conversation_id}",
        headers=headers
    )
    response.raise_for_status()
    return response.json()


def get_cost_breakdown(
    token: str,
    group_by: str = "operation_type"
) -> List[Dict[str, Any]]:
    """
    Get cost breakdown by different dimensions.

    Args:
        token: JWT access token (admin required)
        group_by: Group results by: operation_type, llm_provider, user, date

    Returns:
        List of cost breakdown entries
    """
    headers = {
        "Authorization": f"Bearer {token}"
    }

    params = {"group_by": group_by}

    response = requests.get(
        f"{BASE_URL}/metering/cost-breakdown",
        headers=headers,
        params=params
    )
    response.raise_for_status()
    return response.json()


def calculate_cost(usage: Dict[str, Any]) -> Dict[str, float]:
    """Calculate cost from usage data."""
    provider = usage.get('llm_provider', 'custom_api')
    input_tokens = usage.get('input_tokens', 0)
    output_tokens = usage.get('output_tokens', 0)

    pricing = PRICING.get(provider, PRICING['custom_api'])

    input_cost = (input_tokens / 1_000_000) * pricing['input']
    output_cost = (output_tokens / 1_000_000) * pricing['output']
    total_cost = input_cost + output_cost

    return {
        'input_cost': input_cost,
        'output_cost': output_cost,
        'total_cost': total_cost,
        'provider': provider
    }


def print_user_usage(usage: Dict[str, Any]):
    """Pretty print user usage statistics."""
    print("\n" + "="*80)
    print("USER TOKEN USAGE")
    print("="*80)

    print(f"\nUser ID: {usage['user_id']}")
    print(f"Username: {usage.get('username', 'N/A')}")
    print(f"Period: {usage.get('start_date', 'N/A')} to {usage.get('end_date', 'N/A')}")

    print(f"\n--- Token Statistics ---")
    print(f"Total Input Tokens: {usage['total_input_tokens']:,}")
    print(f"Total Output Tokens: {usage['total_output_tokens']:,}")
    print(f"Total Tokens: {usage['total_tokens']:,}")

    # Cost calculation
    cost = calculate_cost({
        'llm_provider': usage.get('primary_provider', 'custom_api'),
        'input_tokens': usage['total_input_tokens'],
        'output_tokens': usage['total_output_tokens']
    })

    print(f"\n--- Cost Estimation ---")
    print(f"Input Cost: ${cost['input_cost']:.4f}")
    print(f"Output Cost: ${cost['output_cost']:.4f}")
    print(f"Total Cost: ${cost['total_cost']:.4f}")
    print(f"Provider: {cost['provider']}")

    # Usage by operation
    if usage.get('by_operation'):
        print(f"\n--- Usage by Operation ---")
        for op in usage['by_operation']:
            print(f"{op['operation_type']:20s}: {op['tokens']:,} tokens")

    # Usage by provider
    if usage.get('by_provider'):
        print(f"\n--- Usage by Provider ---")
        for prov in usage['by_provider']:
            print(f"{prov['provider']:20s}: {prov['tokens']:,} tokens")

    print("="*80 + "\n")


def print_overall_usage(usage: Dict[str, Any]):
    """Pretty print overall system usage."""
    print("\n" + "="*80)
    print("OVERALL SYSTEM USAGE")
    print("="*80)

    print(f"\n--- Total Statistics ---")
    print(f"Total Users: {usage['total_users']}")
    print(f"Total Conversations: {usage['total_conversations']}")
    print(f"Total Messages: {usage['total_messages']}")
    print(f"Total Tokens: {usage['total_tokens']:,}")

    # Cost calculation
    total_cost = 0
    print(f"\n--- Cost by Provider ---")
    for prov in usage.get('by_provider', []):
        cost = calculate_cost({
            'llm_provider': prov['provider'],
            'input_tokens': prov['input_tokens'],
            'output_tokens': prov['output_tokens']
        })
        total_cost += cost['total_cost']
        print(f"{prov['provider']:20s}: ${cost['total_cost']:.4f} "
              f"({prov['total_tokens']:,} tokens)")

    print(f"\nTotal System Cost: ${total_cost:.4f}")

    # Top users
    if usage.get('top_users'):
        print(f"\n--- Top 5 Users by Token Usage ---")
        for i, user in enumerate(usage['top_users'][:5], 1):
            print(f"{i}. {user['username']:20s}: {user['tokens']:,} tokens")

    print("="*80 + "\n")


def print_cost_breakdown(breakdown: List[Dict[str, Any]], group_by: str):
    """Pretty print cost breakdown."""
    print("\n" + "="*80)
    print(f"COST BREAKDOWN BY {group_by.upper()}")
    print("="*80)

    total_cost = 0

    for entry in breakdown:
        cost = calculate_cost({
            'llm_provider': entry.get('provider', 'custom_api'),
            'input_tokens': entry.get('input_tokens', 0),
            'output_tokens': entry.get('output_tokens', 0)
        })
        total_cost += cost['total_cost']

        key = entry.get(group_by, 'Unknown')
        print(f"\n{key}")
        print(f"  Tokens: {entry.get('total_tokens', 0):,}")
        print(f"  Cost: ${cost['total_cost']:.4f}")
        print(f"  Requests: {entry.get('request_count', 0)}")

    print(f"\n{'─' * 80}")
    print(f"Total Cost: ${total_cost:.4f}")
    print("="*80 + "\n")


def main():
    """Main example workflow."""
    print("=" * 80)
    print("TOKEN USAGE METERING EXAMPLE")
    print("=" * 80)

    # Step 1: Authenticate as admin
    print("\n[1/5] Authenticating as admin...")
    try:
        token = authenticate(ADMIN_USERNAME, ADMIN_PASSWORD)
        print(f"✓ Successfully authenticated")
    except requests.exceptions.HTTPError as e:
        print(f"✗ Authentication failed: {e}")
        return

    # Step 2: Get overall system usage
    print("\n[2/5] Fetching overall system usage...")
    try:
        overall = get_overall_usage(token)
        print(f"✓ Retrieved system usage")
        print_overall_usage(overall)
    except requests.exceptions.HTTPError as e:
        print(f"✗ Failed to get overall usage: {e}")

    # Step 3: Get user-specific usage
    print("\n[3/5] Fetching user-specific usage...")
    # Get first user from overall stats
    if overall.get('top_users'):
        user_id = overall['top_users'][0]['user_id']

        # Last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        try:
            user_usage = get_user_usage(
                token,
                user_id,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            print(f"✓ Retrieved user usage")
            print_user_usage(user_usage)
        except requests.exceptions.HTTPError as e:
            print(f"✗ Failed to get user usage: {e}")

    # Step 4: Get cost breakdown by operation type
    print("\n[4/5] Analyzing cost breakdown by operation...")
    try:
        breakdown_op = get_cost_breakdown(token, "operation_type")
        print(f"✓ Retrieved cost breakdown")
        print_cost_breakdown(breakdown_op, "operation_type")
    except requests.exceptions.HTTPError as e:
        print(f"✗ Failed to get cost breakdown: {e}")

    # Step 5: Get cost breakdown by provider
    print("\n[5/5] Analyzing cost breakdown by provider...")
    try:
        breakdown_prov = get_cost_breakdown(token, "llm_provider")
        print(f"✓ Retrieved provider breakdown")
        print_cost_breakdown(breakdown_prov, "llm_provider")
    except requests.exceptions.HTTPError as e:
        print(f"✗ Failed to get provider breakdown: {e}")

    # Cost optimization tips
    print("\n" + "="*80)
    print("COST OPTIMIZATION TIPS")
    print("="*80)
    print("""
1. Use Ollama for Development/Testing
   • Free local inference (0 cost)
   • Good for prototyping and testing
   • Switch to Custom API for production

2. Optimize Document Chunking
   • Larger chunks = fewer embeddings = lower cost
   • Balance: retrieval accuracy vs cost

3. Enable Response Caching
   • Cache common queries
   • Reduce redundant LLM calls

4. Set Token Limits
   • Max tokens per request
   • Prevent runaway costs

5. Monitor Usage Patterns
   • Identify high-usage users/operations
   • Optimize expensive operations

6. Use Streaming for Better UX
   • Doesn't reduce cost
   • But improves perceived performance

7. Batch Operations Where Possible
   • Combine multiple embeddings
   • Reduce API overhead

8. Choose Right Provider per Task
   • Ollama: Simple queries, development
   • Custom API: Complex reasoning, production
    """)
    print("="*80)

    print("\n✓ Example completed successfully!")


if __name__ == "__main__":
    main()


"""
EXPECTED OUTPUT:
================================================================================
TOKEN USAGE METERING EXAMPLE
================================================================================

[1/5] Authenticating as admin...
✓ Successfully authenticated

[2/5] Fetching overall system usage...
✓ Retrieved system usage

================================================================================
OVERALL SYSTEM USAGE
================================================================================

--- Total Statistics ---
Total Users: 25
Total Conversations: 347
Total Messages: 1,523
Total Tokens: 2,458,932

--- Cost by Provider ---
custom_api          : $0.7892 (1,845,234 tokens)
ollama              : $0.0000 (613,698 tokens)

Total System Cost: $0.7892

--- Top 5 Users by Token Usage ---
1. analyst1@example.com: 456,789 tokens
2. analyst2@example.com: 389,234 tokens
3. viewer1@example.com : 234,567 tokens
4. admin@example.com   : 187,345 tokens
5. analyst3@example.com: 156,234 tokens

================================================================================

[3/5] Fetching user-specific usage...
✓ Retrieved user usage

================================================================================
USER TOKEN USAGE
================================================================================

User ID: 550e8400-e29b-41d4-a716-446655440000
Username: analyst1@example.com
Period: 2024-12-16 to 2025-01-15

--- Token Statistics ---
Total Input Tokens: 234,567
Total Output Tokens: 222,222
Total Tokens: 456,789

--- Cost Estimation ---
Input Cost: $0.0633
Output Cost: $0.2444
Total Cost: $0.3078
Provider: custom_api

--- Usage by Operation ---
chat                : 280,345 tokens
embedding           : 98,234 tokens
analysis            : 45,678 tokens
grounding           : 23,456 tokens
explanation         : 9,076 tokens

--- Usage by Provider ---
custom_api          : 345,678 tokens
ollama              : 111,111 tokens

================================================================================

[4/5] Analyzing cost breakdown by operation...
✓ Retrieved cost breakdown

================================================================================
COST BREAKDOWN BY OPERATION_TYPE
================================================================================

chat
  Tokens: 1,456,789
  Cost: $0.4325
  Requests: 1,234

embedding
  Tokens: 567,890
  Cost: $0.1534
  Requests: 2,345

analysis
  Tokens: 234,567
  Cost: $0.0678
  Requests: 456

grounding
  Tokens: 145,678
  Cost: $0.0423
  Requests: 789

explanation
  Tokens: 54,008
  Cost: $0.0156
  Requests: 234

────────────────────────────────────────────────────────────────────────────────
Total Cost: $0.7116

================================================================================

[5/5] Analyzing cost breakdown by provider...
✓ Retrieved provider breakdown

================================================================================
COST BREAKDOWN BY LLM_PROVIDER
================================================================================

custom_api
  Tokens: 1,845,234
  Cost: $0.7892
  Requests: 3,456

ollama
  Tokens: 613,698
  Cost: $0.0000
  Requests: 1,602

────────────────────────────────────────────────────────────────────────────────
Total Cost: $0.7892

================================================================================

================================================================================
COST OPTIMIZATION TIPS
================================================================================

1. Use Ollama for Development/Testing
   • Free local inference (0 cost)
   • Good for prototyping and testing
   • Switch to Custom API for production

2. Optimize Document Chunking
   • Larger chunks = fewer embeddings = lower cost
   • Balance: retrieval accuracy vs cost

3. Enable Response Caching
   • Cache common queries
   • Reduce redundant LLM calls

4. Set Token Limits
   • Max tokens per request
   • Prevent runaway costs

5. Monitor Usage Patterns
   • Identify high-usage users/operations
   • Optimize expensive operations

6. Use Streaming for Better UX
   • Doesn't reduce cost
   • But improves perceived performance

7. Batch Operations Where Possible
   • Combine multiple embeddings
   • Reduce API overhead

8. Choose Right Provider per Task
   • Ollama: Simple queries, development
   • Custom API: Complex reasoning, production

================================================================================

✓ Example completed successfully!
"""
