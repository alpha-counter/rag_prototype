import os

import httpx
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer


load_dotenv()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth_service:8000").rstrip("/")


async def verify_token(token: str = Depends(oauth2_scheme)):
    async with httpx.AsyncClient() as client:
        payload = {"access_token": token, "token_type": "bearer"}
        response = await client.post(f"{AUTH_SERVICE_URL}/auth/verify-token", json=payload)
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return response.json()
