"""Test HttpMessage streaming methods"""
from bclib.listener import HttpMessage
from bclib.listener.message_type import MessageType

print("=" * 70)
print("HttpMessage Streaming Methods Verification")
print("=" * 70)

# Create HttpMessage
msg = HttpMessage({"test": "data"})

# Check methods
methods = [
    'create_response_message',
    'start_stream_response_async',
    'write_async',
    'drain_async',
    'enable_compression'
]

print("\nChecking methods:")
all_present = True
for method in methods:
    has_method = hasattr(msg, method)
    all_present = all_present and has_method
    status = "✓" if has_method else "✗"
    print(f"  {status} {method}")

print("\n" + "=" * 70)
if all_present:
    print("SUCCESS: All streaming methods are available!")
else:
    print("FAILED: Some methods are missing!")
print("=" * 70)
