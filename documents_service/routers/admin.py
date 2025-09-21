from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, HTTPException, BackgroundTasks
from typing import List
from fastapi.responses import StreamingResponse
from documents_service.utils.authUtil import verify_token
from documents_service.utils.roleCheckerUtil import RoleChecker
from botocore.exceptions import ClientError
from documents_service.services.initTMF_service import create_tmf_structure, read_tmf_structure
from documents_service.utils.s3Util import S3Storage


allow_admin = RoleChecker(["admin"])

# Initialize S3Storage
s3_storage = S3Storage()

class InitializeTMFRequest(BaseModel):
    bucket_name: str
    study_id: str

router = APIRouter(
    prefix="/admin/documents",
    tags=["Admin"],
    dependencies=[Depends(allow_admin)]
)

@router.post("/initialize-tmf")
def initialize_tmf(request: InitializeTMFRequest = Depends(), file: UploadFile = File(...), user: dict = Depends(verify_token)):
    try:
        tmf_structure = read_tmf_structure(file)
        response = create_tmf_structure(request.bucket_name, request.study_id, tmf_structure)
        return response
    except ClientError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/upload/")
async def upload_file(bucket_name: str, file: UploadFile = File(...), user: dict = Depends(verify_token)):
    s3_storage.upload_file(bucket_name, file.file, file.filename)
    return {"filename": file.filename}

@router.post("/upload_folder/")
async def upload_folder(background_tasks: BackgroundTasks, bucket_name: str, files: List[UploadFile] = File(...), user: dict = Depends(verify_token)):
    background_tasks.add_task(s3_storage.upload_folder, bucket_name, files)
    return {"detail": "Folder upload started"}

@router.get("/download/")
def download_file(bucket_name: str, file_name: str, user: dict = Depends(verify_token)):
    file_obj = s3_storage.download_file(bucket_name, file_name)
    return StreamingResponse(file_obj.iter_chunks(), media_type='application/octet-stream', headers={"Content-Disposition": f"attachment;filename={file_name}"})

@router.get("/list/")
def list_files(bucket_name: str, user: dict = Depends(verify_token)):
    files = s3_storage.list_files(bucket_name)
    return {"files": files}

@router.get("/list_folder/")
def list_files_in_folder(bucket_name: str, folder_name: str):
    files = s3_storage.list_files_in_folder(bucket_name, folder_name)
    return {"files": files}

@router.delete("/delete/")
def delete_file(bucket_name: str, file_name: str, user: dict = Depends(verify_token)):
    s3_storage.delete_file(bucket_name, file_name)
    return {"detail": "File deleted"}

@router.post("/create_folder/")
def create_folder(bucket_name: str, folder_name: str, user: dict = Depends(verify_token)):
    s3_storage.create_folder(bucket_name, folder_name)
    return {"detail": "Folder created"}

@router.delete("/delete_folder/")
def delete_folder(bucket_name: str, folder_name: str, user: dict = Depends(verify_token)):
    s3_storage.delete_folder(bucket_name, folder_name)
    return {"detail": "Folder deleted"}

@router.post("/copy_file/")
def copy_file(source_bucket_name: str, source_file_name: str, dest_bucket_name: str, dest_file_name: str, user: dict = Depends(verify_token)):
    s3_storage.copy_file(source_bucket_name, source_file_name, dest_bucket_name, dest_file_name)
    return {"detail": "File copied"}

@router.post("/move_file/")
def move_file(source_bucket_name: str, source_file_name: str, dest_bucket_name: str, dest_file_name: str, user: dict = Depends(verify_token)):
    s3_storage.move_file(source_bucket_name, source_file_name, dest_bucket_name, dest_file_name)
    return {"detail": "File moved"}

@router.post("/copy_folder/")
def copy_folder(source_bucket_name: str, source_folder_name: str, dest_bucket_name: str, dest_folder_name: str):
    s3_storage.copy_folder(source_bucket_name, source_folder_name, dest_bucket_name, dest_folder_name)
    return {"detail": "Folder copied"}

@router.post("/move_folder/")
def move_folder(source_bucket_name: str, source_folder_name: str, dest_bucket_name: str, dest_folder_name: str):
    s3_storage.move_folder(source_bucket_name, source_folder_name, dest_bucket_name, dest_folder_name)
    return {"detail": "Folder moved"}

@router.get("/generate_presigned_url/")
def generate_presigned_url(bucket_name: str, file_name: str, expiration: int = 3600, user: dict = Depends(verify_token)):
    url = s3_storage.generate_presigned_url(bucket_name, file_name, expiration)
    return {"url": url}

@router.post("/make_file_public/")
def make_file_public(bucket_name: str, file_name: str, user: dict = Depends(verify_token)):
    s3_storage.make_file_public(bucket_name, file_name)
    return {"detail": "File made public"}

@router.post("/make_folder_public/")
def make_folder_public(bucket_name: str, folder_name: str, user: dict = Depends(verify_token)):
    s3_storage.make_folder_public(bucket_name, folder_name)
    return {"detail": "Folder made public"}