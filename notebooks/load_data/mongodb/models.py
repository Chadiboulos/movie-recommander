from pydantic import BaseModel, confloat
from typing import List, Optional, Dict
from datetime import datetime


class Tag(BaseModel):
    userid: int
    tag: str
    date: datetime


class Rating(BaseModel):
    movieid: int
    userid: int
    rating: confloat(ge=0.5, le=5.0)
    date: datetime


class Movie(BaseModel):
    movieid: int
    title: str
    genres: List[str]
    genome_scores: Optional[Dict[str, confloat(ge=0, le=1)]]
    ratings:  Optional[List[Rating]]
    imdbid: Optional[int]
    tmdbid: Optional[int]
