import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
required_missing = [
    name for name, val in (
        ("DB_USER", DB_USER),
        ("DB_PASSWORD", DB_PASSWORD),
        ("DB_NAME", DB_NAME)
    ) if not val
]
if required_missing:
    raise RuntimeError(
        f"Missing required environment variables in .env: {', '.join(required_missing)}"
    )
engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    future=True
)
