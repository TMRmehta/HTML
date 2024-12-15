from google.cloud.sql.connector import Connector
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import sqlalchemy
import os

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

USE_LOCAL_DB = os.getenv("USE_LOCAL_DB", "false").lower() == "true"

DB_USER = os.getenv("CLOUDSQL_USER")
DB_PASS = os.getenv("CLOUDSQL_PASSWORD")
DB_NAME = os.getenv("CLOUDSQL_DB")
INSTANCE_CONNECTION_NAME = os.getenv("CLOUDSQL_INSTANCE")

if USE_LOCAL_DB:
    # Local database (Postgres in Docker)
    DB_HOST = os.getenv("LOCAL_DB_HOST", "localhost")
    DB_PORT = os.getenv("LOCAL_DB_PORT", "5432")

    DATABASE_URL = f"postgresql+pg8000://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = sqlalchemy.create_engine(DATABASE_URL)

else:
    # Cloud SQL
    connector = Connector()

    def getconn():
        return connector.connect(
            INSTANCE_CONNECTION_NAME,
            "pg8000",
            user=DB_USER,
            password=DB_PASS,
            db=DB_NAME
        )

    engine = sqlalchemy.create_engine(
        "postgresql+pg8000://",
        creator=getconn
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
