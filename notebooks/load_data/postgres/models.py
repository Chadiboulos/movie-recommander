from typing import Optional

from sqlmodel import Field, SQLModel


class Genre(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    genreid: Optional[int] = Field(default=None, primary_key=True)
    name: str


class Movie (SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    movieid: Optional[int] = Field(default=None, primary_key=True, index=True)
    title: str
    imdbid: Optional[int]
    tmdbid: Optional[int]


class Movie_Genre(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    movieid: int = Field(
        default=None, foreign_key="movie.movieid", primary_key=True, index=True)
    genreid: int = Field(
        default=None, foreign_key="genre.genreid", primary_key=True)


class Tag(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    tagid: int = Field(default=None, primary_key=True)
    userid: int
    movieid: int = Field(default=None, foreign_key="movie.movieid", index=True)
    tag: str
    timestamp: int


class Genome_Tag(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    gtagid: int = Field(default=None, primary_key=True)
    tag: str


class Genome_Score(SQLModel, table=True, extend_existing=True):
    __table_args__ = {'extend_existing': True}
    movieid: int = Field(
        default=None, foreign_key="movie.movieid", primary_key=True, index=True)
    gtagid: int = Field(
        default=None, foreign_key="genome_tag.gtagid", primary_key=True)
    relevance: float = Field(ge=0, le=1)


class Rating (SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    userid: int = Field(default=None, primary_key=True, index=True)
    movieid: int = Field(
        default=None, foreign_key="movie.movieid", primary_key=True, index=True)
    rating: float
    timestamp: int
