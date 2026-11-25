# Milestone F303: A size limit for every Python file, with splits planned, not improvised

> **State:** idea · **Area:** factory
> Planted by the owner on 2026-11-25.

## Notes
from a factory suggestion: "Add a check that fails when a module in runner/ passes 1,800 lines, or imports a module above it outside a function, so runner/loop.py can't grow back into one file."

but configurable number of lines (why 1800?) and for any python code. i do like the idea to ensuring code files don't get massive, the work around it should make sense logically and within the architecture rather than dumb workarounds
