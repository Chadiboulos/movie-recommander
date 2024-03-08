FROM apache/airflow:2.0.2

USER root

COPY --chown=airflow:root ./dags/ \${AIRFLOW_HOME}/dags/

USER airflow