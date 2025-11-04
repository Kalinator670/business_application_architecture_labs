from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class Booking(Base):
    __tablename__ = 'bookings'
    
    booking_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    event_id = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default='confirmed')
    number_of_tickets = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    engine = create_engine('sqlite:///bookings.db')
    Base.metadata.create_all(engine)
    return engine

def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()

