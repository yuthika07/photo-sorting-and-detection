"""
Schemas package — Pydantic models that define the shape of API requests
and responses.

Keeping these separate from db/models.py (Phase 2) matters: schemas are
the *external contract* with the frontend, while DB models are the
*internal representation*. They will diverge over time (e.g. a schema
might hide internal fields or reshape data), so conflating the two
tends to cause painful coupling later.
"""
