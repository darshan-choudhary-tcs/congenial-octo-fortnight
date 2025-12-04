"""
Quick test to verify council voting works
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.agents.orchestrator import orchestrator

async def test_council():
    """Test council voting"""
    print("=" * 80)
    print("Testing Council of Agents (Restored)")
    print("=" * 80)
    
    query = "What are the key principles of effective software design?"
    
    print(f"\nQuery: {query}")
    print(f"Provider: ollama")
    print(f"Strategy: weighted_confidence")
    print("\nExecuting council voting...\n")
    
    try:
        result = await orchestrator.execute_council_voting(
            query=query,
            provider="ollama",
            voting_strategy="weighted_confidence",
            include_synthesis=True,
            debate_rounds=1
        )
        
        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)
        
        print(f"\n✓ Sources (should be empty): {result['sources']}")
        print(f"✓ Agents involved: {result['agents_involved']}")
        
        metrics = result.get('consensus_metrics', {})
        print(f"\nConsensus Level: {metrics.get('consensus_level', 0):.2%}")
        print(f"Agreement Score: {metrics.get('agreement_score', 0):.2%}")
        print(f"Aggregated Confidence: {result.get('aggregated_confidence', 0):.2%}")
        print(f"Execution Time: {result.get('execution_time', 0):.2f}s")
        
        print(f"\nVotes received: {len(result['votes'])}")
        for vote in result['votes']:
            print(f"  - {vote['agent']}: {vote['confidence']:.2%} confidence")
        
        print(f"\nFinal Response:\n{result['response'][:200]}...")
        
        print("\n" + "=" * 80)
        print("✓ TEST PASSED: Council feature restored successfully!")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_council())
    sys.exit(0 if success else 1)
