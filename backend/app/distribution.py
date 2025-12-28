# backend/app/distribution.py

from sqlalchemy.orm import Session
from .models import User, DistributionCounter, project_managers


def get_next_manager(db: Session, project_id: int) -> User:
    """Round-robin распределение менеджеров по проекту"""
    managers = db.query(User).join(
        project_managers,
        User.id == project_managers.c.user_id
    ).filter(
        project_managers.c.project_id == project_id,
        User.role == "manager",
        User.is_active == True
    ).order_by(User.id).all()

    if not managers:
        raise ValueError(f"No active managers in project {project_id}")

    counter = db.query(DistributionCounter).filter(
        DistributionCounter.project_id == project_id
    ).first()

    if not counter:
        counter = DistributionCounter(project_id=project_id, counter=0)
        db.add(counter)
        db.flush()

    selected_manager = managers[counter.counter % len(managers)]

    counter.counter += 1
    db.commit()

    return selected_manager