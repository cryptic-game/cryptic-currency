from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from config import config

uri: str = 'sqlite:///' + config["STORAGE_LOCATION"] + 'wallet.db'

# uri : str = 'mysql://user:password@localhost/database'

engine = create_engine(uri)
Session = sessionmaker(bind=engine)
Base = declarative_base()
session: Session = Session()
