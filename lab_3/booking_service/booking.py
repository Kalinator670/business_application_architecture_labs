import os
from flask import Flask, request, jsonify
import grpc
from datetime import datetime
from user_pb2 import UserRequest
from user_pb2_grpc import UserServiceStub
from event_pb2 import (
    CheckAvailabilityRequest, ReserveSeatsRequest, ReleaseSeatsRequest
)
from event_pb2_grpc import EventServiceStub
from models import init_db, get_session, Booking

app = Flask(__name__)
engine = init_db()
user_host = os.getenv("USER_SERVICE_HOST", "localhost")
user_channel = grpc.insecure_channel(f"{user_host}:50051")
user_client = UserServiceStub(user_channel)
event_host = os.getenv("EVENT_SERVICE_HOST", "localhost")
event_channel = grpc.insecure_channel(f"{event_host}:50052")
event_client = EventServiceStub(event_channel)

@app.route("/api/bookings", methods=["POST"])
def create_booking():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        event_id = data.get("event_id")
        number_of_tickets = data.get("number_of_tickets")
        
        if not all([user_id, event_id, number_of_tickets]):
            return jsonify({"error": "Missing required fields"}), 400
        try:
            user_request = UserRequest(user_id=user_id)
            user_response = user_client.GetUser(user_request)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                return jsonify({"error": f"User with id {user_id} not found"}), 404
            return jsonify({"error": "Error connecting to User Service"}), 500
        try:
            availability_request = CheckAvailabilityRequest(
                event_id=event_id,
                number_of_tickets=number_of_tickets
            )
            availability_response = event_client.CheckAvailability(availability_request)
            
            if not availability_response.available:
                return jsonify({
                    "error": "Not enough seats available",
                    "available_seats": availability_response.available_seats
                }), 400
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                return jsonify({"error": f"Event with id {event_id} not found"}), 404
            return jsonify({"error": "Error connecting to Event Service"}), 500
        
        session = get_session(engine)
        try:
            booking = Booking(
                user_id=user_id,
                event_id=event_id,
                number_of_tickets=number_of_tickets,
                status="confirmed"
            )
            session.add(booking)
            session.commit()
            booking_id = booking.booking_id
        finally:
            session.close()
        
        try:
            reserve_request = ReserveSeatsRequest(
                event_id=event_id,
                number_of_tickets=number_of_tickets,
                booking_id=str(booking_id)
            )
            reserve_response = event_client.ReserveSeats(reserve_request)
            
            if not reserve_response.success:
                session = get_session(engine)
                try:
                    booking = session.query(Booking).filter(Booking.booking_id == booking_id).first()
                    if booking:
                        session.delete(booking)
                        session.commit()
                finally:
                    session.close()
                
                return jsonify({"error": reserve_response.message}), 400
        except grpc.RpcError:
            session = get_session(engine)
            try:
                booking = session.query(Booking).filter(Booking.booking_id == booking_id).first()
                if booking:
                    session.delete(booking)
                    session.commit()
            finally:
                session.close()
            
            return jsonify({"error": "Error reserving seats"}), 500
        
        session = get_session(engine)
        try:
            booking = session.query(Booking).filter(Booking.booking_id == booking_id).first()
            return jsonify({
                "booking_id": booking.booking_id,
                "status": booking.status,
                "message": "Booking created successfully",
                "created_at": booking.created_at.isoformat() + "Z"
            }), 201
        finally:
            session.close()
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/bookings/<int:booking_id>", methods=["GET"])
def get_booking(booking_id):
    session = get_session(engine)
    try:
        booking = session.query(Booking).filter(Booking.booking_id == booking_id).first()
        if booking is None:
            return jsonify({"error": "Booking not found"}), 404
        
        return jsonify({
            "booking_id": booking.booking_id,
            "user_id": booking.user_id,
            "event_id": booking.event_id,
            "status": booking.status,
            "number_of_tickets": booking.number_of_tickets,
            "created_at": booking.created_at.isoformat() + "Z"
        }), 200
    finally:
        session.close()

@app.route("/api/bookings/<int:booking_id>", methods=["DELETE"])
def cancel_booking(booking_id):
    session = get_session(engine)
    try:
        booking = session.query(Booking).filter(Booking.booking_id == booking_id).first()
        if booking is None:
            return jsonify({"error": "Booking not found"}), 404
        
        if booking.status == "cancelled":
            return jsonify({"error": "Booking already cancelled"}), 400
        
        try:
            release_request = ReleaseSeatsRequest(
                event_id=booking.event_id,
                number_of_tickets=booking.number_of_tickets,
                booking_id=str(booking_id)
            )
            release_response = event_client.ReleaseSeats(release_request)
            
            if not release_response.success:
                return jsonify({"error": release_response.message}), 400
        except grpc.RpcError as e:
            return jsonify({"error": "Error releasing seats"}), 500
        booking.status = "cancelled"
        session.commit()
        
        return jsonify({
            "success": True,
            "message": "Booking cancelled successfully"
        }), 200
    finally:
        session.close()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)

