"""
Models package.

Importing each model class here (even though nothing in this file
appears to "use" them) is what makes them register themselves onto
`Base.metadata`. Alembic's autogenerate and any `Base.metadata.create_all()`
call only know about models that have actually been imported somewhere
— this module is that "somewhere", and everything else (session.py,
alembic/env.py) imports models FROM here rather than reaching into
photo.py / face.py / person.py individually.

Adding a new model in a later phase (e.g. Event, Album) is then just:
    1. Create app/db/models/event.py
    2. Import it below and add it to __all__
"""

from app.db.base import Base
from app.db.models.photo import Photo
from app.db.models.face import Face
from app.db.models.person import Person

__all__ = ["Base", "Photo", "Face", "Person"]
