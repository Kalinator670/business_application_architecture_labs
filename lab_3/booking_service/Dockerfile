FROM python:3.9-slim

RUN mkdir /service
COPY protobufs/ /service/protobufs/
COPY booking_service/ /service/booking_service/
WORKDIR /service/booking_service

RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt
RUN python -m grpc_tools.protoc -I ../protobufs --python_out=. \
           --grpc_python_out=. ../protobufs/user.proto ../protobufs/event.proto ../protobufs/booking.proto

EXPOSE 5000
ENV PORT=5000
ENV FLASK_APP=booking.py
ENTRYPOINT [ "python", "booking.py" ]

