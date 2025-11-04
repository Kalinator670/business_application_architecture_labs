from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

class Event(Base):
    __tablename__ = 'events'
    
    event_id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    date = Column(String(50), nullable=False)
    venue = Column(String(100), nullable=False)
    ticket_price = Column(Float, nullable=False)
    total_seats = Column(Integer, nullable=False, default=100)
    
    seats = relationship("Seat", back_populates="event", cascade="all, delete-orphan")

class Seat(Base):
    __tablename__ = 'seats'
    
    seat_id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.event_id'), nullable=False)
    seat_number = Column(Integer, nullable=False)
    is_reserved = Column(Boolean, default=False)
    booking_id = Column(String(50), nullable=True)
    
    event = relationship("Event", back_populates="seats")

def init_db():
    engine = create_engine('sqlite:///events.db')
    Base.metadata.create_all(engine)
    return engine

def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()

