from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# This is your connection to the database
DATABASE_URL = "postgresql://postgres@localhost/taskdb"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

# This gives us a database connection when we need it
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()