FROM apache/airflow:2.8.2

USER root

RUN apt-get update && apt-get install -y gcc python3.11 python3-pip && pip install --upgrade pip && pip install --upgrade setuptools wheel && pip install -r requirements.txt


COPY --chown=airflow:root ./dags/* /opt/airflow/dags

USER airflow