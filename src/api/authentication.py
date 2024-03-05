from datetime import datetime, timedelta
import psycopg2
import jwt
from fastapi import Depends, HTTPException, status
from typing import Optional
from pydantic import BaseModel, Field
from credentials import (pwd_context,
                         SECRET_KEY,
                         ALGORITHM,
                         oauth2_scheme,
                         db_params)


class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int


class Suggestion(BaseModel):
    genre: Optional[str] = Field(None,
                                 description="One or more genres separated by '|'. Example: 'Comedy|Adventure'.")
    start_year: Optional[int] = Field(None,
                                      description="Starting year for filtering movies.")
    end_year: Optional[int] = Field(None,
                                    description="Ending year for filtering movies.")
    decade: Optional[int] = Field(None,
                                  description="Decade for filtering movies.")
    min_duration: Optional[int] = Field(None,
                                        description="Minimum duration for filtering movies.")
    max_duration: Optional[int] = Field(None,
                                        description="Maximum duration for filtering movies.")
    stars: Optional[str] = Field(None,
                                 description="Stars for filtering movies.")
    directors: Optional[str] = Field(None,
                                     description="Directors for filtering movies.")
    certificate: Optional[str] = Field(None,
                                       description="Certificate for filtering movies.")
    writers: Optional[str] = Field(None,
                                   description="Writers for filtering movies.")


class Rating(BaseModel):
    movie_id: int
    rating: float = Field(None,
                          ge=0,
                          le=5)


class Movie(BaseModel):
    title: str
    imdbid: Optional[int] = None
    tmdbid: Optional[int] = None


def verify_password(plain_password, hashed_password):
    """
    Verify whether a plain password matches its hashed counterpart.

    Returns:
    - bool: True if the plain password matches the hashed password, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    Create an access token for authentication.

    Returns:
    - str: The encoded access token as a string.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.api_jwt.encode(
        to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_username(username: str):
    """
    Retrieve user information from the database based on the username.

    Returns:
    - dict: A dictionary containing user information including username, hashed password, user ID, and admin status.
    """
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()

    query = """
        SELECT username, password, userid, is_admin
        FROM users
        WHERE username = %s;
    """

    cursor.execute(query, (f"{username}",))
    users = cursor.fetchall()
    if len(users) == 0:
        raise ValueError()
    users = users[0]
    cursor.close()
    return {"username": users[0],
            "hashed_password": users[1],
            "user_id": users[2],
            "is_admin": users[3]}


def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get the current user based on the provided token.

    Returns:
    - Tuple[dict, int, bool]: A tuple containing user information, including user details dictionary,
      user ID, and admin status.

    Raises:
    - HTTPException: If the credentials cannot be validated or if the user is not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY,
                             algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    user = get_username(username)
    if user is None:
        raise credentials_exception
    user_id = user['user_id']
    is_admin = user['is_admin']
    return user, user_id, is_admin
