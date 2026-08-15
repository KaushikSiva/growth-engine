from sqlalchemy.orm import Session
from ..models import CompanyEvent


def add_event(db: Session, actor: str, action: str, entity_type: str | None = None, entity_id: str | None = None, metadata: dict | None = None) -> CompanyEvent:
    event = CompanyEvent(actor=actor, action=action, entity_type=entity_type, entity_id=entity_id, metadata_json=metadata or {})
    db.add(event)
    db.flush()
    return event
