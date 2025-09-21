from fastapi import Depends, HTTPException, status
from typing import List
from index_service.utils.authUtil import verify_token

class RoleChecker:
    def __init__(self, allowed_roles: List):
        self.allowed_roles = allowed_roles

    def __call__(self, user: dict = Depends(verify_token)):
        if user["user"]["role"].lower() not in self.allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")
