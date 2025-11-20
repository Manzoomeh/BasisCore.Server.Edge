"""Test WebMessage streaming methods"""
from bclib.listener.message_type import MessageType
from bclib.listener.web_message import WebMessage

print("=" * 70)
print("WebMessage Streaming Methods Verification")
print("=" * 70)

# Create WebMessage
msg = WebMessage("test-session", MessageType.AD_HOC, {"test": "data"})

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
