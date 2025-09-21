from fastapi import APIRouter, Depends
from chat_service.utils.authUtil import verify_token

router = APIRouter(
    prefix="/resources",
    tags=["Resources"],
)

@router.get("/")
async def get_resources(user: dict = Depends(verify_token)):
    user_email = user['user']['email']
    return {"message": "Here are your resources", "user_email": user_email}
