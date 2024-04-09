FROM apache/airflow:2.8.2

USER root

COPY --chown=airflow:root ./dags/* /opt/airflow/dags

WORKDIR /opt/airflow/dags

RUN apt-get update && apt-get install -y gcc python3.11 python3-pip

USER airflow

RUN mkdir -p /opt/airflow/temp/model

RUN pip install --upgrade pip && pip install --upgrade setuptools wheel && pip install -r requirements.txt