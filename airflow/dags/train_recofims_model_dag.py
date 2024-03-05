import itertools
from pydantic import BaseModel
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from typing import Optional
import mlflow
import tempfile
import pandas as pd
import os

from surprise import Reader, Dataset, SVD, accuracy
from surprise.model_selection import GridSearchCV

import pickle

train_modele_prdiction_dag = DAG(
    dag_id='train_modele_prediction',
    description="DAG permettant d'entrainer un modèle de prédiction",
    tags=['recofilms'],
    schedule_interval=timedelta(hours=48),
    catchup=False,
    default_args={
        'owner': 'airflow',
        'start_date': datetime(year=2024, month=1, day=5)
    }
)

mlflowserver = Variable.get(key="mlflowserver")
experiment_name = Variable.get(key="experiment_name")
mlflow.set_tracking_uri(mlflowserver)
mlflow.set_experiment(experiment_name)

random_state = 100


class Model_Prediction(BaseModel):
    class_name: Optional[str]
    params: Optional[str]
    mlflow_run_id: str
    mlflow_experiment_name: str
    start_date: datetime
    end_date: Optional[datetime]


def generer_requete_insert_model_prediction(m_p: Model_Prediction):

    return f"""INSERT INTO model_prediction
               (class_name, params,
               mlflow_run_id,
               mlflow_experiment_name,
               start_date, end_date)
        VALUES ('{m_p.class_name}',
                '{m_p.params}',
                '{m_p.mlflow_run_id}',
                '{m_p.mlflow_experiment_name}',
                current_timestamp,
                null)"""


database_url = Variable.get(key="database_uri")
engine = create_engine(database_url)


def init_process():
    print("Process d'entraînement d'un nouveau modèle de prédiction")


def check_connection_database():

    sql_title = "SELECT * FROM rating limit 1 ;"

    with engine.connect() as connection:
        result = connection.execute(text(sql_title))
        for row in result:
            print(row)
            break
    engine.dispose()


def get_list_param_from_param_grid(grid_param):

    params = list()
    for k in grid_param:
        params.append(grid_param[k])
    list_param = list()
    for param in list(itertools.product(*params)):
        list_param.append(dict(zip(grid_param.keys(), param)))
    return list_param


def create_dataset(task_instance):
    sql_rating = """select r.userid,
                    r.movieid,
                    r.rating
                    from rating r
                    order by r."timestamp"
                    limit 1000000;"""

    with engine.connect() as connection:
        result = connection.execute(text(sql_rating)).all()
    df = pd.DataFrame(result)
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    df.to_csv(temp_file)
    task_instance.xcom_push(key='dataset_path', value=temp_file.name)
    print("le dataset est enregistré au chemin: "+temp_file.name)
    engine.dispose()


def train_test_from_dateset_path(dataset_path: str):
    ratings_df = pd.read_csv(dataset_path, index_col=0)
    train_size = int(len(ratings_df) * 0.8)
    reader = Reader(rating_scale=(1, 5))

    train_df = ratings_df.iloc[:train_size]
    test_df = ratings_df.iloc[train_size:]

    # Chargement de l'ensemble d'entraînement
    trainset = Dataset.load_from_df(
        train_df[['userid', 'movieid', 'rating']], reader)

    # Conversion de test_df en liste de tuples pour le testset
    testset = [(uid, iid, r) for (uid, iid, r) in zip(
        test_df['userid'], test_df['movieid'], test_df['rating'])]
    return trainset, testset


def train_model(task_instance, **kwargs):
    dataset_path = task_instance.xcom_pull(key="dataset_path")
    trainset, testset = train_test_from_dateset_path(dataset_path)
    param_grid = {'n_factors': [10],
                  'n_epochs': [20, 50],
                  'lr_all': [0.001, 0.005, 0.02],
                  'reg_all': [0.005, 0.02]}
    context = kwargs

    with mlflow.start_run():
        mlflow.set_tag("type_model", "Surprise_SVD")
        mlflow.set_tag("airflow_dag_run_id", context['dag_run'].run_id)
        gs = GridSearchCV(SVD, param_grid, measures=[
                          "rmse", "mae"], cv=3, n_jobs=-1, refit=True)

        gs.fit(trainset)

        mlflow.log_params(gs.best_params['rmse'])
        best_estimator = gs.best_estimator['rmse']
        predictions = best_estimator.test(testset)
        rmse = accuracy.rmse(predictions)
        mae = accuracy.mae(predictions)
        mlflow.log_metric("rmse", rmse)
        mlflow.log_metric("mae", mae)

        with tempfile.NamedTemporaryFile() as temp_file:
            print("Sauvegarde du modele localisé au: ", temp_file.name)
            with open(temp_file.name, "wb") as f:
                pickle.dump(best_estimator, f)
            mlflow.log_artifact(temp_file.name, "model")


def load_model_from_mlflow_runid(run_id):
    model_path = mlflow.artifacts.download_artifacts(run_id=run_id)
    model_path = os.path.join(model_path, "model")
    model_name = os.listdir(model_path)[0]
    model_path = os.path.join(model_path, model_name)
    model = pickle.load(open(model_path, "rb"))
    return model


def load_model_saved():
    with engine.connect() as connection:
        statement = """select mlflow_run_id
                      from model_prediction
                      where end_date is null;"""
        mlflow_run_id = connection.execute(text(statement)).first()[0]
    return load_model_from_mlflow_runid(mlflow_run_id)


def best_model_runid(task_instance, **kwargs):

    context = kwargs
    experiment = mlflow.get_experiment_by_name(experiment_name)
    experiment_id = experiment.experiment_id
    # metric_name = "metrics.rmse"

    runs = mlflow.search_runs([experiment_id])
    runs = runs[runs['tags.airflow_dag_run_id'] == context['dag_run'].run_id]

    # filtered_runs = runs.dropna(subset=[metric_name])
    # sorted_runs = filtered_runs.sort_values(by=metric_name, ascending=False)

    best_run = runs.iloc[0]
    best_mlflow_runid = best_run.run_id
    task_instance.xcom_push(key="best_model_run_id", value=best_mlflow_runid)


def get_modele_prediction_from(run_id):
    experiment = mlflow.get_experiment_by_name("surprise_recofilms")
    experiment_id = experiment.experiment_id
    runs = mlflow.search_runs([experiment_id])
    model_data = runs[runs.run_id == run_id]
    model = load_model_from_mlflow_runid(run_id)
    m_p = Model_Prediction(class_name=str(model.__class__.__name__),
                           params=str(model_data.filter(
                               regex='params.*').to_json(orient='records')),
                           mlflow_run_id=model_data['run_id'].iloc[0],
                           mlflow_experiment_name="surprise_recofilms",
                           start_date=datetime.now(),
                           end_date=None
                           )
    return m_p


def comparer_choisir_model(task_instance):

    # Chargement du dataset
    dataset_path = task_instance.xcom_pull(key="dataset_path")
    _, testset = train_test_from_dateset_path(dataset_path)

    run_id = task_instance.xcom_pull(key="best_model_run_id")
    best_model = load_model_from_mlflow_runid(run_id)
    model_in_prod = load_model_saved()

    predict_best_model = best_model.test(testset)
    predict_model_saved = model_in_prod.test(testset)
    rmse_best_model = accuracy.rmse(predict_best_model)
    rmse_model_prod = accuracy.rmse(predict_model_saved)

    if rmse_best_model < rmse_model_prod:
        with engine.connect() as connect:
            q_id_model = """select modelid
                            from model_prediction mp
                            where mp.end_date is null ;"""
            mp_id = connect.execute(text(q_id_model)).first()[0]

        mp = get_modele_prediction_from(run_id)
        insert = generer_requete_insert_model_prediction(mp)
        with engine.connect() as connect:
            connect.execute(text(insert))

        with engine.connect() as connect:
            update = f"""update model_prediction
                         set end_date = CURRENT_TIMESTAMP
                         where modelid = {mp_id};"""
            connect.execute(text(update))
        print("Nouveau modèle!!!!!")


my_task1_init = PythonOperator(
    task_id='task1_init',
    python_callable=init_process,
    dag=train_modele_prdiction_dag
)


my_task_check_database = PythonOperator(
    task_id='task2_check_database',
    python_callable=check_connection_database,
    dag=train_modele_prdiction_dag
)


my_task_create_dateset = PythonOperator(
    task_id='task3_create_dateset',
    python_callable=create_dataset,
    dag=train_modele_prdiction_dag
)

my_task_train_model = PythonOperator(
    task_id='task4_train_model',
    python_callable=train_model,
    dag=train_modele_prdiction_dag
)

my_task_find_best_model = PythonOperator(
    task_id='task5_best_model',
    python_callable=best_model_runid,
    dag=train_modele_prdiction_dag
)

my_task_comparer_choisir_model = PythonOperator(
    task_id='task6_comparer_choisir_model',
    python_callable=comparer_choisir_model,
    dag=train_modele_prdiction_dag
)


my_task1_init >> my_task_check_database
my_task_check_database >> my_task_create_dateset
my_task_create_dateset >> my_task_train_model
my_task_train_model >> my_task_find_best_model
my_task_find_best_model >> my_task_comparer_choisir_model
