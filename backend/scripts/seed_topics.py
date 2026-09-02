"""Idempotent seed for the fixed topic catalogue.

Run after `alembic upgrade head`:

    python -m scripts.seed_topics

Keep this list in sync with the Flutter fallback in
`app/lib/src/data/models/topic.dart`.
"""
from __future__ import annotations

from sqlalchemy.dialects.postgresql import insert

from app.db.session import SessionLocal
from app.models import Topic

TOPICS: list[dict] = [
    {"id": "space", "label": "De ruimte", "emoji": "🚀", "sort_order": 10},
    {"id": "animals", "label": "Dieren in het bos", "emoji": "🦊", "sort_order": 20},
    {"id": "ocean", "label": "Onder de zee", "emoji": "🐳", "sort_order": 30},
    {"id": "dinosaurs", "label": "Dinosauriërs", "emoji": "🦕", "sort_order": 40},
    {"id": "dragons", "label": "Vriendelijke draken", "emoji": "🐲", "sort_order": 50},
    {"id": "pirates", "label": "Op de piratenboot", "emoji": "🏴‍☠️", "sort_order": 60},
    {"id": "farm", "label": "Op de boerderij", "emoji": "🐄", "sort_order": 70},
    {"id": "magic", "label": "Toverland", "emoji": "🪄", "sort_order": 80},
    {"id": "trains", "label": "Grote treinen", "emoji": "🚂", "sort_order": 90},
]


def run() -> None:
    with SessionLocal() as db:
        for row in TOPICS:
            stmt = insert(Topic).values(is_active=True, **row)
            stmt = stmt.on_conflict_do_update(
                index_elements=[Topic.id],
                set_={
                    "label": stmt.excluded.label,
                    "emoji": stmt.excluded.emoji,
                    "sort_order": stmt.excluded.sort_order,
                    "is_active": True,
                },
            )
            db.execute(stmt)
        db.commit()
    print(f"seeded {len(TOPICS)} topics")


if __name__ == "__main__":
    run()
