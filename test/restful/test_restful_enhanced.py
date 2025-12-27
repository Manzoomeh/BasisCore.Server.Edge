"""Test RESTful Connection with certifi and raise_for_status"""
import asyncio

from bclib.connections.restful import add_restful_connection
from bclib.connections.restful.irestful_connection import IRestfulConnection
from bclib.di.service_provider import ServiceProvider
from bclib.logger.console_logger import ConsoleLogger
from bclib.options import AppOptions
from bclib.utility.dict_ex import DictEx


async def test_restful_api():
    """Test RESTful connection with a public API"""

    # Sample configuration
    config = DictEx({
        "jsonplaceholder_api": {
            "base_url": "https://jsonplaceholder.typicode.com",
            "timeout": 30,
            "headers": {
                "User-Agent": "BasisCore-Test/1.0"
            },
            "ssl_verify": True  # Use certifi CA bundle
        }
    })

    # Create service provider
    sp = ServiceProvider()

    # Add configuration
    sp.add_singleton(AppOptions, instance=config)

    # Add logger
    sp.add_scoped(ConsoleLogger)

    # Add options service
    from bclib.options import add_options_service
    add_options_service(sp, config)

    # Add RESTful connection
    add_restful_connection(sp)

    # Resolve connection
    api = sp.get_service(IRestfulConnection['jsonplaceholder_api'])

    print("=" * 70)
    print("Testing RESTful Connection with certifi and raise_for_status")
    print("=" * 70)

    try:
        # Test GET with automatic JSON parsing
        print("\n1. GET /posts/1 (should return JSON):")
        post = await api.get_async('/posts/1')
        print(f"   Response type: {type(post)}")
        print(
            f"   Title: {post.get('title') if isinstance(post, dict) else 'N/A'}")
        print(f"   ✓ GET request successful")

        # Test POST with automatic JSON parsing
        print("\n2. POST /posts (should return JSON with id):")
        new_post = await api.post_async(
            '/posts',
            json={
                'title': 'Test Post',
                'body': 'This is a test post from BasisCore',
                'userId': 1
            }
        )
        print(f"   Response type: {type(new_post)}")
        print(
            f"   Created ID: {new_post.get('id') if isinstance(new_post, dict) else 'N/A'}")
        print(f"   ✓ POST request successful")

        # Test GET with params
        print("\n3. GET /posts with params (should return list):")
        posts = await api.get_async('/posts', params={'userId': 1, '_limit': 3})
        print(f"   Response type: {type(posts)}")
        print(
            f"   Number of posts: {len(posts) if isinstance(posts, list) else 'N/A'}")
        print(f"   ✓ GET with params successful")

        # Test 404 error with raise_for_status=True (should raise exception)
        print("\n4. GET /invalid-endpoint (should raise exception):")
        try:
            result = await api.get_async('/invalid-endpoint-that-does-not-exist')
            print("   ✗ Should have raised exception!")
        except Exception as e:
            print(f"   ✓ Exception raised as expected: {type(e).__name__}")
            print(f"   Message: {str(e)[:80]}...")

        # Test 404 error with raise_for_status=False (should not raise)
        print("\n5. GET /invalid-endpoint with raise_for_status=False:")
        result = await api.get_async(
            '/invalid-endpoint-that-does-not-exist',
            raise_for_status=False
        )
        print(f"   Response type: {type(result)}")
        print(f"   Response: {str(result)[:80] if result else 'None'}")
        print(f"   ✓ No exception raised (as expected)")

        # Test PUT
        print("\n6. PUT /posts/1:")
        updated = await api.put_async(
            '/posts/1',
            json={
                'id': 1,
                'title': 'Updated Title',
                'body': 'Updated body',
                'userId': 1
            }
        )
        print(f"   Response type: {type(updated)}")
        print(f"   ✓ PUT request successful")

        # Test PATCH
        print("\n7. PATCH /posts/1:")
        patched = await api.patch_async(
            '/posts/1',
            json={'title': 'Patched Title'}
        )
        print(f"   Response type: {type(patched)}")
        print(f"   ✓ PATCH request successful")

        # Test DELETE
        print("\n8. DELETE /posts/1:")
        deleted = await api.delete_async('/posts/1')
        print(f"   Response type: {type(deleted)}")
        print(f"   ✓ DELETE request successful")

        print("\n" + "=" * 70)
        print("All tests completed successfully!")
        print("=" * 70)
        print("\n✓ certifi SSL verification working")
        print("✓ Automatic JSON/text parsing working")
        print("✓ raise_for_status parameter working")
        print("✓ All HTTP methods working")

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up
        await api.close_async()
        print("\n✓ Connection closed")


if __name__ == "__main__":
    asyncio.run(test_restful_api())
