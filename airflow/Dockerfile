FROM apache/airflow:2.8.2

USER root

COPY --chown=airflow:root ./dags/ \${AIRFLOW_HOME}/dags/

USER airflow