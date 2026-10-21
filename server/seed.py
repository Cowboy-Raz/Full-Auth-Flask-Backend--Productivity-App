"""Reset the database and fill it with example users and notes.

Run from the server/ folder (after `flask db upgrade`):
    python seed.py
"""
import random

from faker import Faker

from app import app
from extensions import db
from models import Note, User

fake = Faker()
# Fixed seeds: same fake data every run
Faker.seed(42)
rng = random.Random(42)

DEMO_PASSWORD = "password123"
USERNAMES = ["demo", "alex", "jordan"]


def seed():
    print("Clearing existing data...")
    Note.query.delete()
    User.query.delete()
    db.session.commit()

    print("Creating users...")
    users = []
    for username in USERNAMES:
        user = User(username=username)
        user.password = DEMO_PASSWORD
        users.append(user)
    db.session.add_all(users)
    db.session.commit()

    print("Creating notes...")
    topics = ["Study", "Workout", "Groceries", "Project", "Idea", "Reading", "Errand"]
    notes = []
    for user in users:
        # 12+ notes each, so pagination (10 per page) has more than one page.
        for _ in range(rng.randint(12, 15)):
            notes.append(
                Note(
                    title=f"{rng.choice(topics)}: {fake.sentence(nb_words=4).rstrip('.')}",
                    content=fake.paragraph(nb_sentences=3),
                    user=user,
                )
            )
    db.session.add_all(notes)
    db.session.commit()

    print(f"Done: {len(users)} users, {len(notes)} notes.")
    print(f"Log in as any of {', '.join(USERNAMES)} with password '{DEMO_PASSWORD}'.")


if __name__ == "__main__":
    with app.app_context():
        seed()
