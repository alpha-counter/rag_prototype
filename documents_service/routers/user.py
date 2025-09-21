from fastapi import APIRouter, Depends
from documents_service.utils.authUtil import verify_token
from documents_service.utils.s3Util import S3Storage

# Initialize S3Storage
s3_storage = S3Storage()

router = APIRouter(
    prefix="/user/documents",
    tags=["User"],
)

@router.get("/list/")
def list_files(bucket_name: str, user: dict = Depends(verify_token)):
    files = s3_storage.list_files(bucket_name)
    return {"files": files}
