FROM ubuntu:22.04

WORKDIR /usr/src/app

COPY . /usr/src/app/

RUN mkdir -p /mlflow/mlruns

RUN apt-get update && apt-get install -y gcc python3.11 python3-pip && pip install --upgrade pip && pip install --upgrade setuptools wheel && pip install -r requirements.txt

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]