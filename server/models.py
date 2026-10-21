"""Database models: User and the user-owned Note resource."""
from extensions import bcrypt, db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    # Only the bcrypt hash is stored, never the plain-text password.
    _password_hash = db.Column("password_hash", db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    # Deleting a user also deletes their notes.
    notes = db.relationship(
        "Note", back_populates="user", cascade="all, delete-orphan", lazy="dynamic"
    )

    @property
    def password(self):
        raise AttributeError("Password is write-only.")

    @password.setter
    def password(self, plaintext):
        self._password_hash = bcrypt.generate_password_hash(plaintext).decode("utf-8")

    def authenticate(self, plaintext):
        """Return True if `plaintext` matches the stored hash."""
        return bcrypt.check_password_hash(self._password_hash, plaintext)

    def __repr__(self):
        return f"<User {self.id} {self.username}>"


class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    user = db.relationship("User", back_populates="notes")

    def __repr__(self):
        return f"<Note {self.id} user={self.user_id} {self.title!r}>"
