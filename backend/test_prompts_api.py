"""
Test script for Prompts API endpoints
Requires admin user credentials
"""
import requests
import json
from typing import Optional

BASE_URL = "http://localhost:8000/api/v1"

# Test credentials (replace with actual admin credentials)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # Change this to your admin password

def get_auth_token() -> Optional[str]:
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        }
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def test_list_prompts(token: str):
    """Test GET /prompts endpoint"""
    print("\n📋 Testing: List all prompts")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/prompts", headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Found {data['total']} prompts")
        print(f"   Categories: {', '.join(data['categories'])}")
        print(f"   First 3 prompts: {', '.join([p['name'] for p in data['prompts'][:3]])}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_list_by_category(token: str, category: str = "agent"):
    """Test GET /prompts?category=agent endpoint"""
    print(f"\n📋 Testing: List prompts by category '{category}'")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/prompts?category={category}", headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Found {data['total']} prompts in category '{category}'")
        print(f"   Prompts: {', '.join([p['name'] for p in data['prompts']])}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_get_categories(token: str):
    """Test GET /prompts/categories endpoint"""
    print("\n📋 Testing: Get categories")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/prompts/categories", headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Found {len(data['categories'])} categories")
        for cat, count in data['count_by_category'].items():
            print(f"   - {cat}: {count} prompts")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_get_stats(token: str):
    """Test GET /prompts/stats endpoint"""
    print("\n📋 Testing: Get usage statistics")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/prompts/stats", headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success!")
        print(f"   Total prompts: {data['total_prompts']}")
        print(f"   Built-in: {data['built_in_prompts']}, Custom: {data['custom_prompts']}")
        print(f"   Total usage: {data['total_usage']}")
        if data['most_used']:
            print(f"   Most used: {data['most_used'][0]['name']} ({data['most_used'][0]['usage_count']} times)")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_get_prompt(token: str, name: str = "research_analyst"):
    """Test GET /prompts/{name} endpoint"""
    print(f"\n📋 Testing: Get prompt '{name}'")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/prompts/{name}", headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success!")
        print(f"   Name: {data['name']}")
        print(f"   Category: {data['category']}")
        print(f"   Description: {data['description']}")
        print(f"   Variables: {', '.join(data['variables']) if data['variables'] else 'None'}")
        print(f"   Is custom: {data['is_custom']}")
        print(f"   Template preview: {data['template'][:100]}...")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_create_custom_prompt(token: str):
    """Test POST /prompts endpoint"""
    print("\n📋 Testing: Create custom prompt")
    headers = {"Authorization": f"Bearer {token}"}

    prompt_data = {
        "name": "test_custom_prompt",
        "template": "Analyze the following topic: {topic}\n\nProvide insights on: {focus}",
        "category": "custom",
        "description": "Test custom prompt for API validation",
        "variables": ["topic", "focus"],
        "output_format": "text",
        "purpose": "Testing API functionality"
    }

    response = requests.post(
        f"{BASE_URL}/prompts",
        headers=headers,
        json=prompt_data
    )

    if response.status_code == 201:
        data = response.json()
        print(f"✅ Success! Created prompt '{data['name']}'")
        print(f"   Category: {data['category']}")
        print(f"   Variables: {', '.join(data['variables'])}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_update_custom_prompt(token: str):
    """Test PUT /prompts/{name} endpoint"""
    print("\n📋 Testing: Update custom prompt")
    headers = {"Authorization": f"Bearer {token}"}

    update_data = {
        "description": "Updated test custom prompt description",
        "template": "Analyze the following topic: {topic}\n\nProvide detailed insights on: {focus}\n\nConsider: {additional_context}"
    }

    response = requests.put(
        f"{BASE_URL}/prompts/test_custom_prompt",
        headers=headers,
        json=update_data
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Updated prompt '{data['name']}'")
        print(f"   New description: {data['description']}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_test_prompt(token: str):
    """Test POST /prompts/{name}/test endpoint"""
    print("\n📋 Testing: Test prompt with variables")
    headers = {"Authorization": f"Bearer {token}"}

    test_data = {
        "variables": {
            "topic": "Artificial Intelligence",
            "focus": "machine learning applications",
            "additional_context": "current industry trends"
        }
    }

    response = requests.post(
        f"{BASE_URL}/prompts/test_custom_prompt/test",
        headers=headers,
        json=test_data
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success!")
        print(f"   Formatted prompt preview:")
        print(f"   {data['formatted_prompt'][:200]}...")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_delete_custom_prompt(token: str):
    """Test DELETE /prompts/{name} endpoint"""
    print("\n📋 Testing: Delete custom prompt")
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.delete(
        f"{BASE_URL}/prompts/test_custom_prompt",
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! {data['message']}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_protected_operations(token: str):
    """Test that built-in prompts are protected"""
    print("\n📋 Testing: Protection of built-in prompts")
    headers = {"Authorization": f"Bearer {token}"}

    # Try to update a built-in prompt
    print("   Attempting to update built-in prompt 'research_analyst'...")
    update_data = {"description": "Modified description"}
    response = requests.put(
        f"{BASE_URL}/prompts/research_analyst",
        headers=headers,
        json=update_data
    )

    if response.status_code == 403:
        print(f"   ✅ Correctly rejected update: {response.json()['detail']}")
    else:
        print(f"   ❌ Should have rejected with 403, got {response.status_code}")

    # Try to delete a built-in prompt
    print("   Attempting to delete built-in prompt 'research_analyst'...")
    response = requests.delete(
        f"{BASE_URL}/prompts/research_analyst",
        headers=headers
    )

    if response.status_code == 403:
        print(f"   ✅ Correctly rejected delete: {response.json()['detail']}")
        return True
    else:
        print(f"   ❌ Should have rejected with 403, got {response.status_code}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Prompts API Test Suite")
    print("=" * 60)

    # Get authentication token
    print("\n🔐 Authenticating...")
    token = get_auth_token()
    if not token:
        print("\n❌ Cannot proceed without authentication token")
        print("Please ensure:")
        print("  1. Backend server is running on http://localhost:8000")
        print("  2. Admin user credentials are correct")
        return

    print("✅ Authentication successful")

    # Run all tests
    tests = [
        lambda: test_list_prompts(token),
        lambda: test_list_by_category(token),
        lambda: test_get_categories(token),
        lambda: test_get_stats(token),
        lambda: test_get_prompt(token),
        lambda: test_create_custom_prompt(token),
        lambda: test_update_custom_prompt(token),
        lambda: test_test_prompt(token),
        lambda: test_delete_custom_prompt(token),
        lambda: test_protected_operations(token),
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Success rate: {passed/total*100:.1f}%")

    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")

if __name__ == "__main__":
    main()
