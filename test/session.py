from sqlalchemy.engine import URL
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# TODO: Derive this from _something_
url = URL.create(
    drivername="postgresql+psycopg",
    username="postgres",
    host="localhost",
    database="oban_py_test",
)


def create_session():
    engine = create_engine(url)
    Session = sessionmaker(bind=engine)

    return Session()
