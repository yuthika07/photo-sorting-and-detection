"""
Shared dependency-injection providers.

FastAPI's dependency injection system (the `Depends(...)` you'll see in
router function signatures) lets a route declare "I need X" without
knowing how X is constructed. This module is where those "how to build
X" functions live, so routers stay declarative and testable — in tests,
you can override any of these with `app.dependency_overrides[...]`
without touching route code at all.

Phase 7 adds a DBSessionDep alias wiring in Phase 2's get_db(). AI-model
providers may be added here in a later phase if a router needs them
directly; routers will keep depending on the same *names*, so adding
those later won't require changing any existing router signatures.
"""

# Used for type-hinting what get_logger() returns
import logging

from fastapi import Depends
from typing import Annotated

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db


def get_logger(
    settings: Annotated[Settings, Depends(get_settings)],
) -> logging.Logger:
    """
    Provide a module-scoped logger for use inside route handlers.

    Args:
        settings: injected app Settings (unused directly here today, but
            kept as a dependency so this provider can be extended later
            — e.g. to attach a request-scoped log level — without
            changing its call signature in every router).

    Returns:
        A standard library Logger instance named "app.api", so log lines
        from route handlers are clearly distinguishable from core/
        or service-layer log lines.
    """
    return logging.getLogger("app.api")


# Type aliases so router signatures read cleanly, e.g.:
#     def health(settings: SettingsDep, logger: LoggerDep): ...
# instead of repeating the full Annotated[...] expression everywhere.
SettingsDep = Annotated[Settings, Depends(get_settings)]
LoggerDep = Annotated[logging.Logger, Depends(get_logger)]

# get_db (Phase 2, in app/db/session.py) already yields a Session with
# proper open/close lifecycle management per request — this alias just
# gives routers the same short, readable injection syntax as the two
# aliases above, without duplicating that lifecycle logic here.
DBSessionDep = Annotated[Session, Depends(get_db)]
