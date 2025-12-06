"""Debug string annotations"""
from __future__ import annotations
from bclib.options import IOptions
from typing import get_type_hints
import inspect

import sys

sys.path.insert(
    0, 'd:/Programming/Falsafi/BasisCore/Server/BasisCore.Server.Edge')


class MyService:
    def __init__(self, db_options: IOptions['database']):
        self.db_options = db_options


print("=== Analyzing MyService.__init__ ===\n")

# Check __annotations__
print(f"__annotations__: {MyService.__init__.__annotations__}")
print()

# Try get_type_hints
try:
    hints = get_type_hints(MyService.__init__)
    print(f"get_type_hints: {hints}")
except Exception as e:
    print(f"get_type_hints failed: {e}")
    print(f"  Error type: {type(e).__name__}")
print()

# Check signature
sig = inspect.signature(MyService.__init__)
for name, param in sig.parameters.items():
    print(f"Parameter '{name}':")
    print(f"  annotation: {param.annotation}")
    print(f"  annotation type: {type(param.annotation)}")
