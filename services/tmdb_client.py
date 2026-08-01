import requests
from config import TMDB_ACCESS_TOKEN

BASE_URL = "https://api.themoviedb.org/3"

_headers = {
    "Authorization": f"Bearer {TMDB_ACCESS_TOKEN}",
    "accept": "application/json",
}

def get_genres():
    response = requests.get(f"{BASE_URL}/genre/movie/list", headers=_headers)
    response.raise_for_status()
    return response.json()["genres"]


def get_credits(movie_tmdb_id):
    response = requests.get(f"{BASE_URL}/movie/{movie_tmdb_id}/credits", headers=_headers)
    response.raise_for_status()
    data = response.json()
    return {
        "cast": data.get("cast", []),
        "crew": data.get("crew", []),
    }


def get_movies(page=1, date_gte=None, date_lte=None):
    params = {
        "page": page,
        "sort_by": "popularity.desc",
    }
    if date_gte is not None:
        params["primary_release_date.gte"] = date_gte
    if date_lte is not None:
        params["primary_release_date.lte"] = date_lte

    response = requests.get(
        f"{BASE_URL}/discover/movie",
        headers=_headers,
        params=params,
    )
    response.raise_for_status()
    data = response.json()
    return {
        "results": data["results"],
        "page": data["page"],
        "total_pages": min(data["total_pages"], 500),
    }
