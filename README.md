# MovieFlix

Ce répertoire est dédié au projet de fin de notre formation MLOps.

Le service livré consiste en des recommandations personnalisées et intelligentes de films en fonction de l'historique de notations des clients.

Ceux qui n'ont pas assez d'historique ou les prospects pourront avoir des recommandations basées sur une liste de critères tels que le genre, la décennie de sortie, le réalisateur etc.


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

Retrouvez les instructions d'installation sur un cluster Kubernetes sur ce [GitHub](https://github.com/Jbdu4493/oct23_cmlops_reco_films_helm).
