import json
import logging
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from src.db.models import ProviderModel

logger = logging.getLogger(__name__)

_SEED_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "providers_seed.json"


def load_provider_seed() -> list[dict[str, str]]:
    with _SEED_PATH.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError(f"Expected list in {_SEED_PATH}")
    return data


def seed_providers(session_factory: sessionmaker[Session]) -> int:
    """Insert providers from JSON when the table is empty. Returns rows inserted."""
    seed_rows = load_provider_seed()
    with session_factory() as session:
        count = session.scalar(select(func.count()).select_from(ProviderModel)) or 0
        if count > 0:
            return 0
        for row in seed_rows:
            session.add(
                ProviderModel(
                    id=row["id"],
                    name=row["name"],
                    specialty=row["specialty"],
                    next_slot=row["next_slot"],
                )
            )
        session.commit()
        inserted = len(seed_rows)
        logger.info("Seeded %d providers", inserted)
        return inserted
