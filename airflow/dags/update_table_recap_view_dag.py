from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

update_table_recap_view_dag = DAG(
    dag_id='update_table_recap_view',
    description='DAG permettant de mettre\
        à jour la vue materialiser "table_recap_view"',
    tags=['recofilms'],
    schedule_interval=timedelta(hours=1),
    catchup=False,
    default_args={
        'owner': 'airflow',
        'start_date': datetime(year=2024, month=1, day=5)
    }
)


def init_process():
    print('Process de mise à jour de la vue "table_recap_view"')


def check_connection_database():
    database_url = Variable.get(key="database_uri")
    engine = create_engine(database_url)
    sql_title = "SELECT * FROM table_recap_view;"

    with engine.connect() as connection:
        result = connection.execute(text(sql_title))
        for row in result:
            print(row)
            break

    engine.dispose()


def update_view():
    database_url = Variable.get(key="database_uri")
    engine = create_engine(database_url)
    sql_title = "REFRESH MATERIALIZED VIEW table_recap_view;"

    with engine.connect() as connection:
        connection.execute(text(sql_title))

    engine.dispose()


my_task1_init = PythonOperator(
    task_id='task1_init',
    python_callable=init_process,
    dag=update_table_recap_view_dag
)

my_task_check_database = PythonOperator(
    task_id='task2_check',
    python_callable=check_connection_database,
    dag=update_table_recap_view_dag
)

my_task_update_view = PythonOperator(
    task_id='task3_update',
    python_callable=update_view,
    dag=update_table_recap_view_dag
)

my_task1_init >> my_task_check_database >> my_task_update_view
