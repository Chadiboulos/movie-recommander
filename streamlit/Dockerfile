FROM ubuntu:22.04

WORKDIR /usr/src/app

COPY . /usr/src/app/

RUN apt-get update && apt-get install -y python3.11 python3-pip && pip install --upgrade pip && pip install -r requirements.txt

EXPOSE 8504

CMD ["streamlit", "run", "front.py", "--server.port", "8504"]