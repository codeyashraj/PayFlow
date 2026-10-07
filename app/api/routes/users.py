from fastapi import APIRouter
from app.api.dependencies import CurrentUser
from app.schemas.auth import UserResponse
router=APIRouter(prefix="/api/v1/users",tags=["users"])
@router.get("/me",response_model=UserResponse)
async def me(current_user:CurrentUser): return current_user
