from fastapi import APIRouter, Depends
from typing import List
from index_service.utils.authUtil import verify_token
from index_service.utils.roleCheckerUtil import RoleChecker
from pydantic import BaseModel
from index_service.services.indexing import IndexService

allow_admin = RoleChecker(["admin"])

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    # dependencies=[Depends(allow_admin)]
)

class IngestRequest(BaseModel):
    source_directory: str
    storage_type: str

index = IndexService()

@router.post("/index_all", status_code=200)
async def index_all_documents(request: IngestRequest):
    result = index.all(request.source_directory, request.storage_type)
    return result
