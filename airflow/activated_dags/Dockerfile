FROM ubuntu:latest

WORKDIR /sources/

COPY ./* /sources/

RUN apt-get upgrade && apt-get update && apt-get install python3 python3-pip python3-requests -y

CMD ["python3","activated_dags.py"]