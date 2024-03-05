from pydantic import BaseModel
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from typing import Optional
import mlflow
import pandas as pd
import os
import pickle
from surprise import Reader, Dataset, SVD, accuracy
from surprise.model_selection import train_test_split, GridSearchCV


train_modele_prdiction_dag2 = DAG(
    dag_id='train_modele_prediction2',
    description="DAG permettant d'entrainer un modele prédiction",
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

database_url = Variable.get(key="database_uri")
engine = create_engine(database_url)


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


def init_process():
    print("Process d'entrainement d'un nouveau modele de prédiction")


def check_connection_database():
    sql_title = "SELECT * FROM rating limit 1 ;"
    with engine.connect() as connection:
        result = connection.execute(text(sql_title))
        for row in result:
            print(row)
            break
    engine.dispose()


def train_model(task_instance, **kwargs):
    context = kwargs
    
    # load 100k dataset from DB
    sql_rating = """select r.userid,
                r.movieid,
                r.rating
                from rating r 
                order by r."timestamp" 
                limit 100000;"""

    with engine.connect() as connection:
        result = connection.execute(text(sql_rating)).all()
    engine.dispose()
    
    # Transform dataset to surprise format and split
    reader = Reader(line_format=u'user item rating timestamp', sep=',', rating_scale=(1, 5), skip_lines=1)
    df = pd.DataFrame(result)
    data = Dataset.load_from_df(df[['userid', 'movieid', 'rating']], reader=reader) 

    # Make manual train_test_split, Trainset = 75% of the data, Testset = 25% of the data
    raw_ratings = data.raw_ratings  # data in list format - 100 000 lines
    threshold = int(0.75 * len(raw_ratings))
    trainset_raw_ratings = raw_ratings[:threshold]
    testset_raw_ratings = raw_ratings[threshold:]
    data.raw_ratings = trainset_raw_ratings  # data is now the Trainset - 75 000 lines
    
    # Make trainset suitable for fit() function
    trainset = data.build_full_trainset()
    
    # Make testset suitable for test() function
    testset = data.construct_testset(testset_raw_ratings)
    
    param_grid = {'n_factors': [30],'n_epochs': [20],'lr_all': [0.02, 0.025, 0.03],'reg_all': [0.005, 0.1, 0.15]}

    # run mlflow engine
    with mlflow.start_run():
        mlflow.set_tag("type_model", "Surprise_SVD")
        mlflow.set_tag("airflow_dag_run_id", context['dag_run'].run_id)
        
        # search best parameters for model
        grid_search = GridSearchCV(SVD, param_grid, measures=["rmse", "mae"], cv=3, n_jobs=-1, refit=True)
        grid_search.fit(data)
        
        # get best model from GridSearchCV - best_estimator, and make predictions with it
        mlflow.log_params(grid_search.best_params['rmse'])
        best_estimator = grid_search.best_estimator['rmse']
        best_estimator.fit(trainset)
        predictions = best_estimator.test(testset)
        
        # log metrics to mlflow server
        rmse = accuracy.rmse(predictions)
        mae = accuracy.mae(predictions)
        mlflow.log_metric("rmse", rmse)
        mlflow.log_metric("mae", mae)
        
        # save best model to mlflow server
        # set tag mlflow_run_id to see run IDs for all runs on mlflow web page
        experiment_name = Variable.get(key="experiment_name")
        mlflow_current_run_id = mlflow.active_run().info.run_id
        mlflow.set_tag("mlflow_run_id", mlflow_current_run_id)
        
        # get model local path
        model_local_path = os.path.join("/home/ritz/MLflow/mlruns_local", experiment_name)
        model_name = os.path.join(model_local_path, mlflow_current_run_id)
        model_full_path = os.path.join(model_local_path, model_name)
        model_full_path_pkl = os.path.join(model_full_path, "model.pkl")
        
        # 1) save model and 100k_data.csv locally
        mlflow.sklearn.save_model(best_estimator, model_full_path)
        dataset_path = os.path.join(model_full_path, "100k_data.csv")
        df.to_csv(dataset_path)
        
        # 2) save model (just one model.pkl file) from local folder to MLflow server
        mlflow.log_artifact(model_full_path_pkl, artifact_path="model")
        
        # 3) log_model save all model files (model.pkl, requirements.txt, conda.yaml ...) to MLflow server
        mlflow.sklearn.log_model(best_estimator, "model_sklearn")
        
    task_instance.xcom_push(key='dataset_path', value=dataset_path)


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


def find_best_model(task_instance, **kwargs):
    context = kwargs
    experiment = mlflow.get_experiment_by_name(experiment_name)
    experiment_id = experiment.experiment_id
    metric_name = "metrics.rmse"

    runs = mlflow.search_runs([experiment_id])
    runs = runs[runs['tags.airflow_dag_run_id'] == context['dag_run'].run_id]

    filtered_runs = runs.dropna(subset=[metric_name])
    sorted_runs = filtered_runs.sort_values(by=metric_name, ascending=False)

    best_run = sorted_runs.iloc[0]
    best_run_id = best_run.run_id
    task_instance.xcom_push(key="best_model_run_id", value=best_run_id)


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
    
    # Load 100k_data.csv dataset
    # dataset_path = model_local_path + "/100k_data.csv"
    data_df = pd.read_csv(dataset_path, sep=",", names=['userid','movieid','rating'], header = 0)
    reader = Reader(rating_scale=(1, 5))
    data = Dataset.load_from_df(data_df, reader=reader)
    _, testset = train_test_split(data, test_size=0.25)
    # _, testset = train_test_from_dateset_path(dataset_path)

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


task1_init = PythonOperator(
    task_id='task1_init',
    python_callable=init_process,
    dag=train_modele_prdiction_dag2
)


task2_check_database = PythonOperator(
    task_id='task2_check_database',
    python_callable=check_connection_database,
    dag=train_modele_prdiction_dag2
)


task3_train_model = PythonOperator(
    task_id='task3_train_model',
    python_callable=train_model,
    dag=train_modele_prdiction_dag2
)


task4_find_best_model = PythonOperator(
    task_id='task4_best_model',
    python_callable=find_best_model,
    dag=train_modele_prdiction_dag2
)

task5_comparer_choisir_model = PythonOperator(
    task_id='task5_comparer_choisir_model',
    python_callable=comparer_choisir_model,
    dag=train_modele_prdiction_dag2
)


task1_init >> task2_check_database
task2_check_database >> task3_train_model
task3_train_model >> task4_find_best_model
task4_find_best_model >> task5_comparer_choisir_model