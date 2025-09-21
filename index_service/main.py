from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from index_service.routers import admin
import uvicorn
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    docs_url="/docs",
    redoc_url="/redocs",
    title="Resource Service API",
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

app.include_router(admin.router)

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8001)
## uvicorn index_service.main:app --reload --port 8001