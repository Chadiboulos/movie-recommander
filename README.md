# MovieFlix

Ce répertoire est dédié au projet de fin de notre formation **MLOps**. Application et services associés déploient un système de recommandation de films dans un environnement **Kubernetes local**.

Le service livré consiste en des recommandations personnalisées et intelligentes de films basées sur l'historique de notation des clients.

Ceux qui n'ont pas assez d'historique ou les prospects pourront avoir des recommandations basées sur une liste de critères tels que le genre, la décennie de sortie, le réalisateur etc.

L'interface client repose sur un Streamlit qui lui-même dépend d'une API dockerisée contenant une multitude d'endpoints.

En plus de ce repo, un repo Github dédié à l'architecture kubernetes est disponible ici <a href="https://github.com/Jbdu4493/oct23_cmlops_reco_films_helm">Movieflix_Helm</a>

Nous avons visé plusieurs objectifs avec notre architecture:
 - <ins>**High Availability**</ins>: assurer une haute disponibilité à notre service en le déployant avec Kubernetes
 - <ins>**Continuous Training**</ins>: offrir à nos clients, à tout moment la version la plus performante de notre algorithme via Airflow et mlflow
 - <ins>**Continuous Integration**</ins>: mettre entre les mains de nos clients la version fonctionnelle la plus récente de notre code intégrant les films les plus récents via Git Workflow/pytest et du webscraping (Beautiful Soup)
 - <ins>**Continuous Deployment**</ins>: faire en sorte que toute modification du code ou toute évolution souhaitée de l'architecture se reflète automatiquement sur le déploiement actuel via Kubernetes (argoCD et Helm)
 - <ins>**Continuous Monitoring**</ins>: suivre de façon continue l'activité de notre API via Grafana et Prometheus

![Screenshot](https://github.com/Chadiboulos/movie-recommander/blob/main/notebooks/Architecture.png?raw=true)


## Organisation du Projet

```
├── airflow
│   └── dags <- Dossiers pour les Directed Acyclic Graphs (DAGs), utilisés                                                                                                                                      pour programmer et ordonnancer des tâches automatiquement.
│   ├── train_recofilms_model_dag.py <- DAG pour l'entraînement du modèle de recommandation.
│   ├── update_table_recap_view_dag.py <- DAG pour la mise à jour des vues récapitulatives dans une base de données.
│   └── webscraping_dag.py <- DAG pour le web scraping.
├── grafana_dashboard
│   └── dashboard_movieflix.json <- Configuration pour un tableau de bord Grafana, utilisé pour la visualisation de données.
├── k8s
│   ├── k8s-config.yaml <- Configuration de Kubernetes pour le déploiement de l'application.
│   └── setup_node_master_worker.sh <- Script pour configurer les nœuds maître et travailleur dans un cluster Kubernetes.
├── notebooks
│   ├── load_data <- Notebooks Jupyter pour le chargement des données.
│   └── webscrapping_imdb.ipynb <- Notebook pour le web scraping de données IMDb.
├── src
│   └── api
│   ├── Dockerfile <- Pour construire un conteneur Docker pour l'API.
│   ├── authentication.py <- Gère l'authentification pour l'API.
│   ├── create_image.sh <- Script pour créer une image Docker de l'API.
│   ├── credentials.py <- Stocke les identifiants pour l'API et de la base de données.
│   ├── main.py <- Point d'entrée principal pour l'API, toutes les routes sont implémentées dans ce fichier.
│   ├── mlflow_model.py <- Fonction permettant de charger un modèle dans MLflow.
│   ├── requirements.txt <- Liste des dépendances Python pour faire fonctionner l'API.
│   ├── svd_model.pkl <- Un modèle sauvegardé.
│   ├── test_*.py <- Contient des tests unitaires pour l'API.
│   ├── utilities.py <- Fonctions diverses pour l'API.
│   └── welcome.py <- Gère le message de bienvenue de l'API.
└── streamlit
    ├── Dockerfile <- Pour construire un conteneur Docker pour l'application Streamlit.
    ├── create_image.sh <- Script pour créer une image Docker de l'application Streamlit.
    ├── front.py <- Application Streamlit pour une interface web interactive.
    └── requirements.txt <- Liste des dépendances Python pour l'application Streamlit.
```

## Installation de l'application

Retrouvez les instructions d'installation sur un cluster Kubernetes sur ce [Movieflix_Helm](https://github.com/Jbdu4493/oct23_cmlops_reco_films_helm).
