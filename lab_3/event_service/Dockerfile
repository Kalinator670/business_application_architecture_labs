FROM python:3.9-slim

RUN mkdir /service
COPY protobufs/ /service/protobufs/
COPY event_service/ /service/event_service/
WORKDIR /service/event_service

RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt
RUN python -m grpc_tools.protoc -I ../protobufs --python_out=. \
           --grpc_python_out=. ../protobufs/event.proto

EXPOSE 50052
ENV PORT=50052
ENTRYPOINT [ "python", "event.py" ]

