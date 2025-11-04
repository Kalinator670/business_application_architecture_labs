from concurrent import futures
import grpc
import os
from user_pb2 import UserRequest, UserResponse
import user_pb2_grpc
from models import init_db, get_session, User

class UserService(user_pb2_grpc.UserServiceServicer):
    def __init__(self):
        self.engine = init_db()
        self._init_sample_data()
    
    def _init_sample_data(self):
        session = get_session(self.engine)
        try:
            if session.query(User).count() == 0:
                sample_users = [
                    User(user_id=1, name="Иван Иванов", email="ivan@example.com", phone="+79001234567"),
                    User(user_id=2, name="Мария Петрова", email="maria@example.com", phone="+79007654321"),
                    User(user_id=3, name="Алексей Сидоров", email="alex@example.com", phone="+79001112233"),
                ]
                session.add_all(sample_users)
                session.commit()
        finally:
            session.close()
    
    def GetUser(self, request, context):
        session = get_session(self.engine)
        try:
            user = session.query(User).filter(User.user_id == request.user_id).first()
            if user is None:
                context.abort(grpc.StatusCode.NOT_FOUND, f"User with id {request.user_id} not found")
            
            return UserResponse(
                user_id=user.user_id,
                name=user.name,
                email=user.email,
                phone=user.phone or ""
            )
        finally:
            session.close()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    port = os.getenv("PORT", "50051")
    server.add_insecure_port(f"[::]:{port}")
    print(f"User Service starting on port {port}")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()

