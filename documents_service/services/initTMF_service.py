import boto3
import os
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File

def read_tmf_structure(file: UploadFile):
    tmf_structure = {}
    current_zone = None

    with file.file as f:
        for line in f:
            line = line.decode('utf-8').strip()
            if not line:
                continue
            if line.startswith("Zone"):
                current_zone = line
                tmf_structure[current_zone] = []
            else:
                if current_zone is not None:
                    tmf_structure[current_zone].append(line)
    
    return tmf_structure

def create_tmf_structure(bucket_name, study_id, tmf_structure):
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_DEFAULT_REGION')
    )
    
    base_path = f"tmf/{study_id}/"

    for zone, sections in tmf_structure.items():
        for section in sections:
            folder_path = f"{base_path}{zone}/{section}/"
            s3_client.put_object(Bucket=bucket_name, Key=folder_path)

    return {"message": "TMF structure initialized successfully."}
