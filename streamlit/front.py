import streamlit as st
import requests
import numpy as np
import os
APIURL = os.environ.get("APIURL", "http://localhost:8001")


def afficher_films(movied: int, predict_rating: float = None):
    response = requests.get(url=APIURL + "/movie_details/" + str(movied), headers={'accept': 'application/json'})
    donnees_film = response.json()
    
    if not donnees_film:  # Check for empty list or None
        return ""

    html = "<div style='display:flex;flex-direction:column;align-items:center;padding:10px;'>"

    # Handle predict_rating
    st.write(f"### ID Movie: {movied}")
    pourcent = f"{int((predict_rating/5) * 100)}%" if predict_rating is not None else ""
    title = donnees_film.get('title', 'Unknown Title')
    html += f"<h2>{title} {pourcent}</h2>"

    # Handle poster
    poster = donnees_film.get('poster', '')
    if poster:
        html += f"<img src='{poster}' alt='Poster' style='width:200px;height:auto;border-radius:10px;box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);'>"

    # Extract and handle None values for all fields
    summary = donnees_film.get('summary', 'No summary available')
    avg_rating = donnees_film.get('avg_rating', 0.0) or 0.0  # Ensure a float
    nb_rating = donnees_film.get('nb_rating', 'No ratings') or 'No ratings'
    directors = donnees_film.get('directors', 'Unknown') or 'Unknown'
    genre = donnees_film.get('genre', 'Unknown') or 'Unknown'
    writers = donnees_film.get('writers', 'Unknown') or 'Unknown'
    stars = donnees_film.get('stars', 'Unknown') or 'Unknown'
    duration = donnees_film.get('duration', 'Unknown') if donnees_film.get('duration') else 'Unknown'

    html += f"""<div style='margin-top:10px;'>
                <p><strong>Résumé:</strong> {summary}</p>
                <p><strong>Note moyenne:</strong> {avg_rating:.2f} / 5 (sur {nb_rating} avis)</p>
                <p><strong>Réalisateurs:</strong> {directors}</p>
                <p><strong>Genre:</strong> {genre}</p>
                <p><strong>Scénaristes:</strong> {writers}</p>
                <p><strong>Acteurs principaux:</strong> {stars}</p>
                <p><strong>Durée:</strong> {duration} minutes</p>
            </div>
            </div>
    """
    return html




def get_movie_rating():
    if 'token' not in st.session_state:
        return []
    response = requests.get(APIURL + "/previously_rated_movies/",
                            headers={'accept': 'application/json',
                                     'Authorization': 'Bearer ' + st.session_state.token,
                                     'Content-Type': 'application/json'
                                     }
                            )
    return response.json()


def connect(user: str, password: str):
    response = requests.post(url=APIURL+'/token',
                             headers={
                                 'accept': 'application/json',
                                 'Content-Type': 'application/x-www-form-urlencoded'},
                             data={'username': user,
                                   'password': password
                                   })
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(response.json())


with st.sidebar:
    st.header("Connexion")
    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type="password")
    if st.button("Connexion"):
        try:
            if 'token' not in st.session_state:
                st.session_state.token = connect(username, password)
        except Exception as e:
            st.write(f"Problème d'authentification 😭 {e}")
    if 'token' in st.session_state:
        st.write("Vous êtes connecté 👌🏿")
    else:
        st.write("⚠️ Vous n'êtes pas connecté")


# Création des onglets principaux
tab1, tab2, tab3, tab4 = st.tabs(
    ["Suggestions", "Films Notés", "Noter Films ", "Recherche"])


def generer_liste_annees(debut, fin):
    return list(range(debut, fin + 1))


with tab1:
    st.header("Suggestion")
    if st.button("Recommendations"):
        try:
            response = requests.get(
                url=APIURL+"/client_recommendation/",
                headers={'accept': 'application/json',
                            'Authorization': 'Bearer ' + st.session_state.token}
            )
            if response.status_code == 200:
                recommendations = response.json().get("recommendations")
                for r in recommendations:
                    st.write(afficher_films(r.get("movieid"),
                                            r.get("predicted_rating")
                                            ),
                                unsafe_allow_html=True
                                )
                    st.write("------")
        except Exception as e :
            st.write("Ce service est réservé uniquement aux clients authentifiés. Pour obtenir des\
                      recommandations veuillez saisir vos préférences dans l'onglet 'Recherche'")
            print(e)


def afficher_etoiles(note):
    note_arrondie = round(note * 2) / 2
    etoiles_pleines = int(note_arrondie)
    demi_etoile = note_arrondie - etoiles_pleines
    etoiles = '⭐️' * etoiles_pleines
    if demi_etoile:
        etoiles += '✨'
    return etoiles


with tab2:
    if st.button("Voir les films que j'ai déjà notés"):
        movie_ratings = get_movie_rating()
        for movie in movie_ratings:
            st.write("------")
            movie_details = afficher_films(int(movie['movieid']))
            st.write(movie_details, unsafe_allow_html=True)
            st.write("Note attribuée: " +
                     afficher_etoiles(movie['rating']) +
                     f"({movie['rating']}/5)")

with tab3:
    id_movies = st.text_input("id du film à noter")

    if id_movies != "":
        id_movies = int(id_movies)
        movie_ratings = get_movie_rating()
        find = list(filter(lambda x: x["movieid"]
                    == id_movies, movie_ratings))

        movie_details = afficher_films(int(id_movies))
        if movie_details != "":
            st.write(movie_details, unsafe_allow_html=True)
            if len(find) != 0:
                st.write(
                    f" ⚠️  Vous avez déjà donné une note de **{find[0]['rating']}** pour ce film. Vous pouvez néanmoins modifier cette note")
                txt_bouton = "Modifier note"

            else:
                txt_bouton = "Noter"
            note = st.selectbox(
                "Choisir une note",
                np.arange(.5, 5.1, .5),
                index=0,
                placeholder="Choisir une note...",
            )

            note = float(note)
            movieid = int(id_movies)
        if st.button(txt_bouton):
            response = requests.post(APIURL + "/rate_movie/",
                                     headers={'accept': 'application/json',
                                              'Authorization': 'Bearer ' + st.session_state.token,
                                              'Content-Type': 'application/json'
                                              },
                                     json={"movie_id": movieid,
                                           "rating": note}
                                     )
            if response.status_code == 200:
                st.write("Film noté!!! 👍")
            else:
                st.write("Problème survenu lors de la notation du film!! 😡")
        if len(find) != 0:
            if st.button("Supprimer Note"):
                response = requests.delete(APIURL + '/delete_rate/'+str(movieid),
                                           headers={'accept': 'application/json',
                                                    'Authorization': 'Bearer ' + st.session_state.token,
                                                    'Content-Type': 'application/json'}
                                           )
                if response.status_code == 200:
                    st.write("Note supprimée!!! 👍")
                else:
                    st.write("Problème survenu lors de la suppression de la note!! 😡 ")


with tab4:

    genre = st.text_input("Genre", "")
    stars = st.text_input("Stars", "")
    directors = st.text_input("Réalisateurs", "")
    writers = st.text_input("Scénaristes", "")
    start_year = st.selectbox("Année de début", [0] + generer_liste_annees(
        1900, 2024), format_func=lambda x: 'Sélectionner' if x == 0 else x)
    end_year = st.selectbox("Année de fin", [0] + generer_liste_annees(
        1900, 2024), format_func=lambda x: 'Sélectionner' if x == 0 else x)
    decade = st.selectbox("Décennie", [
                          0] + list(range(1900, 2021, 10)), format_func=lambda x: 'Sélectionner' if x == 0 else x)
    min_duration = st.number_input(
        "Durée minimale (en minutes)", min_value=0, max_value=500, step=10, value=0)
    max_duration = st.number_input(
        "Durée maximale (en minutes)", min_value=0, max_value=500, step=10, value=0)

    # Initialisation du dictionnaire
    informations_film = {}

    # Ajout conditionnel des valeurs dans le dictionnaire
    if genre:
        informations_film["genre"] = genre
    if stars:
        informations_film["stars"] = stars
    if directors:
        informations_film["directors"] = directors
    if writers:
        informations_film["writers"] = writers
    if start_year > 0:
        informations_film["start_year"] = int(start_year)
    if end_year > 0:
        informations_film["end_year"] = int(end_year)
    if decade > 0:
        informations_film["decade"] = int(decade)
    if min_duration > 0:
        informations_film["min_duration"] = int(min_duration)
    if max_duration > 0:
        informations_film["max_duration"] = int(max_duration)
    if st.button("Rechercher"):
        response = requests.post(APIURL + '/prospect_suggestion',
                                 headers={
                                     'Content-Type': 'application/json',
                                 }, json=informations_film)
        if response.status_code == 200:
            movies = response.json()["top_movies"]
            if len(movies) == 0:
                st.write('Pas de films répondant à ce(s) critère(s) 🤓 ')
            else:
                st.session_state.movies = movies
                for m in movies:
                    st.write(afficher_films(
                        m['movieid']), unsafe_allow_html=True)
                    if 'token' in st.session_state:
                        movie_ratings = get_movie_rating()

                        find = list(filter(lambda x: x["movieid"] == m['movieid'],
                                           movie_ratings))
                        if len(find) != 0:
                            st.write(
                                f"✅ Le film a déjà été noté **{find[0]['rating']}**")
