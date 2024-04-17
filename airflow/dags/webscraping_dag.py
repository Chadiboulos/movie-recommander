from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
import requests
from bs4 import BeautifulSoup
get_imdb_data_dag = DAG(
    dag_id='webscraping_imdb',
    description='DAG permettant de recuperer les donnée de films sur imdb"',
    tags=['recofilms'],
    schedule_interval=timedelta(minutes=20),
    catchup=False,
    default_args={
        'owner': 'airflow',
        'start_date': datetime(year=2024, month=1, day=5)
    }
)


def init_process():
    print('Process de recuperation de donnée imdb')


def check_connection_database():
    database_url = Variable.get(key="database_uri")
    engine = create_engine(database_url)
    sql_title = "SELECT 'OK' FROM imdb_data limit 1;"

    with engine.connect() as connection:
        result = connection.execute(text(sql_title))
        for row in result:
            print(row)
            break

    engine.dispose()


def check_imdb_site():
    url = "https://www.imdb.com/title/tt0112401/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\
              (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    print("before request")
    response = requests.get(url, headers=headers)
    print("after request")
    if response.status_code == 200:
        print("OK")
    else:
        raise Exception("Error IMDB pas accessible")


def get_real_scenarist_stars(soup):
    lis = soup.find_all("ul", attrs={
                        "class": "ipc-metadata-list ipc-metadata-list--dividers-all title-pc-list ipc-metadata-list--baseAlt"})[0]
    meta_data = list()
    for _, li in enumerate(lis):
        data = list(li.strings)
        meta_data.append(data[0:])
    realisateur, scenarist, stars = list(), list(), list()
    for data in meta_data:
        if data[0].startswith("Director"):
            realisateur = data[1:]
        if data[0].startswith("Writer"):
            scenarist = data[1:]
        if data[0].startswith("Star"):
            stars = data[1:]
    return realisateur, scenarist, stars


def get_summary(soup):
    summary = soup.find_all("span", attrs={"class": "sc-466bb6c-1 dWufeH"})[0]

    if list(summary):
        summary = list(summary)[0]
    else:
        summary = ''
    return summary


def get_public_access_duration(soup):
    items = list()
    uls = soup.find_all("ul", attrs={
                        "class": "ipc-inline-list ipc-inline-list--show-dividers sc-d8941411-2 cdJsTz baseAlt"})
    for ul in uls:
        for lis in ul.find_all('li'):
            for li in lis:
                for text_ in li.strings:
                    items.append(text_)
    return items[-2:]


def get_affiche_url(soup):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\
              (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    div = soup.find_all("div", attrs={
                        "class": "ipc-poster ipc-poster--baseAlt ipc-poster--dynamic-width ipc-sub-grid-item ipc-sub-grid-item--span-2"})
    try:
        imge_url = "https://www.imdb.com/" + div[0].find_all("a")[0]['href']
        response = requests.get(imge_url, headers=headers)

        if response.status_code == 200:
            soup_image = BeautifulSoup(response.content, 'html.parser')
        return soup_image.find_all("img", srcset=True)[0]["srcset"].split(",")[-2].split()[0]
    except IndexError:
        return ''


def scrape_imdb(imdb_id):
    print("scrape_imdb")
    url = f"https://www.imdb.com/title/tt{imdb_id}/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        # Exemple pour extraire le titre du film
        title_tag = soup.find('h1')
        summary = get_summary(soup)
        title = title_tag.text.strip()
        try:
            pub_acc, duration = get_public_access_duration(soup)
        except ValueError:
            print(get_public_access_duration(soup))
            pub_acc, duration = '', ''

        affiche_url = get_affiche_url(soup)
        realisateur, scenarist, stars = get_real_scenarist_stars(soup)

        return {
            "titre": title,
            "summary": summary,
            "certificat": pub_acc,
            "duration": duration,
            "poster": affiche_url,
            "directors": '|'.join(realisateur),
            "writers": '|'.join(scenarist),
            "stars": '|'.join(stars)


        }
    else:
        raise ValueError


def get_sql(film_data):
    columns = ', '.join(film_data.keys())
    placeholders = ', '.join(["'"+str(film_data[fd]).replace("'", "''")+"'"
                              for fd in film_data.keys()])
    sql = """INSERT INTO imdb_data({})
             VALUES ({});""".format(columns, placeholders)
    return sql


def search_imdb_data():
    database_url = Variable.get(key="database_uri")
    engine = create_engine(database_url)
    query = """
        SELECT m.imdbid,m.movieid
        FROM movie m
        inner join movie tr on tr.movieid = m.movieid
        left outer join imdb_data id on id.movieid = tr.movieid
        where id.movieid is null
        order by random()
        limit 200;
        """
    with engine.connect() as connection:
        imdbid = connection.execute(text(query))
        list_imdb = list(imdbid)
        list_imdb = list(map(lambda x: (f"{x[0]:07}",
                                        x[1]), list_imdb))
        for imdb, movieid in list_imdb:
            try:
                movie_data = scrape_imdb(imdb)
                movie_data['movieid'] = movieid
                sql = get_sql(movie_data)
                connection.execute(text(sql))
            except Exception:
                print(movieid, imdb)
    engine.dispose()


my_task1_init = PythonOperator(
    task_id='task1_init',
    python_callable=init_process,
    dag=get_imdb_data_dag
)

my_task_check_database = PythonOperator(
    task_id='task2_check_database',
    python_callable=check_connection_database,
    dag=get_imdb_data_dag
)

my_task_check_imdb = PythonOperator(
    task_id='task3_check_imdb',
    python_callable=check_imdb_site,
    dag=get_imdb_data_dag
)

my_task_get_imdb_data = PythonOperator(
    task_id='task3_get_imdb_date',
    python_callable=search_imdb_data,
    dag=get_imdb_data_dag
)

my_task1_init >> my_task_check_database >> my_task_get_imdb_data
my_task1_init >> my_task_check_imdb >> my_task_get_imdb_data
