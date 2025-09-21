from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from auth_service import models
from auth_service.utils.dbUtil import engine
from auth_service.routers import auth, user,admin
import uvicorn
from dotenv import load_dotenv

load_dotenv()

## -------------------------------- Database connection initialization --------------------------------
models.Base.metadata.create_all(bind=engine)

## -------------------------------- App initialization --------------------------------
app = FastAPI(
    docs_url="/docs",
    redoc_url="/redocs",
    title="Authentication API",
    description="",
    version="0.1.0",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

## -------------------------------- Register Route for {Authentication} -------------------------------
app.include_router(auth.router)
## -------------------------------- Register Route for {Admin} -------------------------------
app.include_router(admin.router)
## -------------------------------- Register Route for {User} -------------------------------
app.include_router(user.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
## uvicorn auth_service.main:app --reload --port=8000