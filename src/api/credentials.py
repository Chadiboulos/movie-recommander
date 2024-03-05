from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
oauth2_admin_scheme = OAuth2PasswordBearer(tokenUrl="token/admin")  # not used

# Configuration pour le JWT
SECRET_KEY = os.environ.get('SECRET_KEY')
ALGORITHM = os.environ.get('ALGORITHM')
ACCESS_TOKEN_EXPIRATION = int(os.environ.get('ACCESS_TOKEN_EXPIRATION'))
# Database credentials
db_params = {
    'dbname': os.environ.get('DBNAME'),
    'user': os.environ.get("USER"),
    'password': os.environ.get("PASSWORD"),
    'host': os.environ.get("HOST"),
    'port': os.environ.get("PORT")
}
