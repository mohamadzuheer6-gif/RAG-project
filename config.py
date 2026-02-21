import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

    # Railway provides DATABASE_URL automatically for PostgreSQL
    database_url = os.getenv("DATABASE_URL")

    if database_url and database_url.startswith("postgres://"):
        # Fix for SQLAlchemy + Railway old postgres scheme
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    
    