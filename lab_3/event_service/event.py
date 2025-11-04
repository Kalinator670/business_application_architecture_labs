from concurrent import futures
import grpc
import os
from event_pb2 import (
    CheckAvailabilityRequest, CheckAvailabilityResponse, EventInfo,
    ReserveSeatsRequest, ReserveSeatsResponse,
    ReleaseSeatsRequest, ReleaseSeatsResponse
)
import event_pb2_grpc
from models import init_db, get_session, Event, Seat

class EventService(event_pb2_grpc.EventServiceServicer):
    def __init__(self):
        self.engine = init_db()
        self._init_sample_data()
    
    def _init_sample_data(self):
        session = get_session(self.engine)
        try:
            if session.query(Event).count() == 0:
                event1 = Event(
                    event_id=101,
                    name="Концерт симфонического оркестра",
                    date="2024-02-20T19:00:00Z",
                    venue="Концертный зал",
                    ticket_price=2500.0,
                    total_seats=100
                )
                event2 = Event(
                    event_id=102,
                    name="Театральная постановка 'Гамлет'",
                    date="2024-02-25T18:00:00Z",
                    venue="Драматический театр",
                    ticket_price=1800.0,
                    total_seats=150
                )
                session.add(event1)
                session.add(event2)
                session.commit()
                
                for i in range(1, 101):
                    seat = Seat(event_id=101, seat_number=i, is_reserved=False)
                    session.add(seat)
                
                for i in range(1, 151):
                    seat = Seat(event_id=102, seat_number=i, is_reserved=False)
                    session.add(seat)
                
                session.commit()
        finally:
            session.close()
    
    def CheckAvailability(self, request, context):
        session = get_session(self.engine)
        try:
            event = session.query(Event).filter(Event.event_id == request.event_id).first()
            if event is None:
                context.abort(grpc.StatusCode.NOT_FOUND, f"Event with id {request.event_id} not found")
            
            available_seats = session.query(Seat).filter(
                Seat.event_id == request.event_id,
                Seat.is_reserved == False
            ).count()
            
            available = available_seats >= request.number_of_tickets
            
            event_info = EventInfo(
                event_id=event.event_id,
                name=event.name,
                date=event.date,
                venue=event.venue,
                ticket_price=event.ticket_price
            )
            
            return CheckAvailabilityResponse(
                available=available,
                available_seats=available_seats,
                event=event_info
            )
        finally:
            session.close()
    
    def ReserveSeats(self, request, context):
        session = get_session(self.engine)
        try:
            event = session.query(Event).filter(Event.event_id == request.event_id).first()
            if event is None:
                context.abort(grpc.StatusCode.NOT_FOUND, f"Event with id {request.event_id} not found")
            
            available_seats = session.query(Seat).filter(
                Seat.event_id == request.event_id,
                Seat.is_reserved == False
            ).limit(request.number_of_tickets).all()
            
            if len(available_seats) < request.number_of_tickets:
                return ReserveSeatsResponse(
                    success=False,
                    message=f"Not enough seats available. Requested: {request.number_of_tickets}, Available: {len(available_seats)}"
                )
            
            seat_numbers = []
            for seat in available_seats:
                seat.is_reserved = True
                seat.booking_id = request.booking_id
                seat_numbers.append(seat.seat_number)
            
            session.commit()
            
            return ReserveSeatsResponse(
                success=True,
                message="Seats reserved successfully",
                seat_numbers=seat_numbers
            )
        except Exception as e:
            session.rollback()
            context.abort(grpc.StatusCode.INTERNAL, f"Error reserving seats: {str(e)}")
        finally:
            session.close()
    
    def ReleaseSeats(self, request, context):
        session = get_session(self.engine)
        try:
            seats = session.query(Seat).filter(
                Seat.event_id == request.event_id,
                Seat.booking_id == request.booking_id,
                Seat.is_reserved == True
            ).all()
            
            if not seats:
                return ReleaseSeatsResponse(
                    success=False,
                    message=f"No seats found for booking {request.booking_id}"
                )
            
            for seat in seats:
                seat.is_reserved = False
                seat.booking_id = None
            
            session.commit()
            
            return ReleaseSeatsResponse(
                success=True,
                message="Seats released successfully"
            )
        except Exception as e:
            session.rollback()
            context.abort(grpc.StatusCode.INTERNAL, f"Error releasing seats: {str(e)}")
        finally:
            session.close()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    event_pb2_grpc.add_EventServiceServicer_to_server(EventService(), server)
    port = os.getenv("PORT", "50052")
    server.add_insecure_port(f"[::]:{port}")
    print(f"Event Service starting on port {port}")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()

