FROM python:3.9-slim

RUN mkdir /service
COPY protobufs/ /service/protobufs/
COPY user_service/ /service/user_service/
WORKDIR /service/user_service

RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt
RUN python -m grpc_tools.protoc -I ../protobufs --python_out=. \
           --grpc_python_out=. ../protobufs/user.proto

EXPOSE 50051
ENV PORT=50051
ENTRYPOINT [ "python", "user.py" ]

