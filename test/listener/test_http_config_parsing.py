"""Simple unit test for HttpListener options parsing"""


def parse_http_config(http_config):
    """Parse http config and return list of normalized configs"""
    if isinstance(http_config, str):
        # Simple string: "localhost:8080"
        return [{"endpoint": http_config}]
    elif isinstance(http_config, list):
        # Array of configs
        configs = []
        for item in http_config:
            if isinstance(item, str):
                # String item in array
                configs.append({"endpoint": item})
            elif isinstance(item, dict):
                # Dict item in array
                configs.append(item)
        return configs
    elif isinstance(http_config, dict):
        # Single dict config
        return [http_config]
    else:
        return []


def test_parsing():
    """Test http config parsing logic"""
    print("="*70)
    print(" " * 20 + "HTTP Config Parsing Tests")
    print("="*70 + "\n")

    # Test 1: Simple string
    print("Test 1: Simple string")
    result = parse_http_config("localhost:8080")
    print(f"  Input: \"localhost:8080\"")
    print(f"  Output: {result}")
    assert len(result) == 1
    assert result[0] == {"endpoint": "localhost:8080"}
    print("  ✅ PASS\n")

    # Test 2: Array of strings
    print("Test 2: Array of strings")
    result = parse_http_config(["localhost:8080", "localhost:8081"])
    print(f"  Input: [\"localhost:8080\", \"localhost:8081\"]")
    print(f"  Output: {result}")
    assert len(result) == 2
    assert result[0] == {"endpoint": "localhost:8080"}
    assert result[1] == {"endpoint": "localhost:8081"}
    print("  ✅ PASS\n")

    # Test 3: Array with dict
    print("Test 3: Array with mixed strings and dicts")
    result = parse_http_config([
        "localhost:8080",
        {"endpoint": "localhost:8443", "ssl": {"certfile": "cert.pem"}}
    ])
    print(f"  Input: [\"localhost:8080\", {{...}}]")
    print(f"  Output: {result}")
    assert len(result) == 2
    assert result[0] == {"endpoint": "localhost:8080"}
    assert result[1]["endpoint"] == "localhost:8443"
    assert "ssl" in result[1]
    print("  ✅ PASS\n")

    # Test 4: Single dict
    print("Test 4: Single dict")
    result = parse_http_config({"endpoint": "localhost:8080", "ssl": {}})
    print(f"  Input: {{\"endpoint\": \"localhost:8080\", ...}}")
    print(f"  Output: {result}")
    assert len(result) == 1
    assert result[0]["endpoint"] == "localhost:8080"
    print("  ✅ PASS\n")

    # Test 5: Array of dicts
    print("Test 5: Array of dicts")
    result = parse_http_config([
        {"endpoint": "localhost:8080"},
        {"endpoint": "localhost:8443", "ssl": {"certfile": "cert.pem"}},
        {"endpoint": "0.0.0.0:9000", "config": {"router": "restful"}}
    ])
    print(f"  Input: [{{...}}, {{...}}, {{...}}]")
    print(f"  Output count: {len(result)} configs")
    assert len(result) == 3
    assert result[0]["endpoint"] == "localhost:8080"
    assert result[1]["endpoint"] == "localhost:8443"
    assert result[2]["endpoint"] == "0.0.0.0:9000"
    print("  ✅ PASS\n")

    print("="*70)
    print("✅ ALL PARSING TESTS PASSED!")
    print("\nSupported formats:")
    print("  1. String: \"localhost:8080\"")
    print(
        "  2. Array of strings: [\"localhost:8080\", \"localhost:8081\", ...]")
    print(
        "  3. Dict: {\"endpoint\": \"...\", \"ssl\": {...}, \"config\": {...}}")
    print("  4. Array of dicts: [{...}, {...}, ...]")
    print("  5. Mixed array: [\"localhost:8080\", {...}, ...]")
    print("="*70)


if __name__ == "__main__":
    test_parsing()
