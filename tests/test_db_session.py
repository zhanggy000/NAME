from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.db.session import create_db_engine, get_db


def test_create_db_engine_supports_sqlite_memory():
    engine = create_db_engine("sqlite+pysqlite:///:memory:")
    Session = sessionmaker(bind=engine)

    with Session() as session:
        assert session.execute(text("SELECT 1")).scalar_one() == 1


def test_get_db_yields_session_and_closes_it():
    db = next(get_db())
    try:
        assert db is not None
    finally:
        db.close()
