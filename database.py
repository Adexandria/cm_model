from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.models.user import Base
from api.crud import create_role

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
    db.close()
    print("Database initialized with default roles.")

if __name__ == "__main__":
    init_db()