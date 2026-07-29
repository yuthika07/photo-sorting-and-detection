"""
Core package — cross-cutting concerns used by the entire application:
configuration, logging setup, and shared exception types.

Nothing in this package should import from api/, services/, db/, or ai/ —
core is the foundation everything else builds on, so it must have zero
dependencies on higher layers.
"""
