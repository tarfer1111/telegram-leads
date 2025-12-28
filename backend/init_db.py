# backend/init_db.py

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User
from app.auth import get_password_hash


def init_database():
    """Создает админа если его нет"""

    db = SessionLocal()

    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=get_password_hash("admin123"),
                role="admin",
                full_name="System Administrator",
                is_active=True
            )
            db.add(admin)
            db.commit()
            print("✅ Admin created: admin / admin123")
        else:
            print("✅ Admin already exists")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_database()