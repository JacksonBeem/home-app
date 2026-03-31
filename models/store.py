# store.py

from sqlalchemy import Column, Integer, String, Numeric, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import database

Base = declarative_base()


class Store(Base):

    __tablename__ = "store"

    upc = Column(Integer, primary_key=True, autoincrement=True)

    item_name = Column(String(255), nullable=False)

    brand = Column(String(255))

    store_location = Column(String(50))

    old_price = Column(Numeric(10, 2))

    new_price = Column(Numeric(10, 2))

    price_change = Column(Numeric(10, 2))

    last_checked = Column(DateTime, default=datetime.utcnow)


def create_tables():

    Base.metadata.create_all(database.engine)