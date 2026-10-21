"""Flask extension objects.

They are created here without an app and attached to it in app.create_app().
Keeping them in their own module lets models.py import `db` without importing
app.py, which avoids circular imports.
"""
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

# Predictable constraint names keep Alembic migrations working on SQLite.
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)

db = SQLAlchemy(metadata=metadata)
migrate = Migrate()
bcrypt = Bcrypt()
