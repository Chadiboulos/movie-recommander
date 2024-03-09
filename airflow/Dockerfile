FROM apache/airflow:2.8.2

USER root

COPY --chown=airflow:root ./dags/* /opt/airflow/dags

USER airflow