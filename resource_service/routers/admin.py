from fastapi import APIRouter, Depends
from typing import List
from resource_service.utils.authUtil import verify_token
from resource_service.utils.roleCheckerUtil import RoleChecker

allow_admin = RoleChecker(["admin"])

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(allow_admin)]
)

@router.get("/protected-resource", status_code=200)
async def get_protected_resource(user: dict = Depends(verify_token)):
    return {"message": "This is a protected resource", "user_email": user["user"]["email"]}
