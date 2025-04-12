from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from bot.database.models import Base
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_session():
    return Session()