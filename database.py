from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.models.user import Base
from api.crud import create_role, add_default_admin_user_v1, add_default_admin_user_v2, add_test_user

DATABASE_URL = "sqlite:///./test.db"

"""Database setup and session management."""
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

"""Dependency to get a database session."""
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize the database."""
    db = SessionLocal()
    create_role(db)
    add_default_admin_user_v2(db)
    add_default_admin_user_v1(db)
    add_test_user(db)
    db.close()
    print("Database initialized with default roles.")

if __name__ == "__main__":
    init_db()