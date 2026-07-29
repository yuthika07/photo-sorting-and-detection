"""
API package — the HTTP boundary of the application.

Everything here (routers + dependency providers) should stay thin: parse
the request, call a dependency or service, shape the response. Business
logic belongs in services/ (Phase 2+), not here.
"""
