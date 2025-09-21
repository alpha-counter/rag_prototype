from fastapi import HTTPException, status
from passlib.context import CryptContext

## ---------------------------- Hashing --------------------------------
## For password encryption and verfications
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify(plain, hashed):
    return pwd_context.verify(plain, hashed) # bycrypt also automatically salts the password


def get_hash(value):
    return pwd_context.hash(value)