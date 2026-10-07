from fastapi import APIRouter,HTTPException,Request,status
from app.api.dependencies import DBSession
from app.schemas.auth import UserRegisterRequest,UserLoginRequest,UserResponse,TokenResponse
from app.services.auth import AuthService
from app.core.exceptions import AuthenticationError,ConflictError
from app.services.rate_limit import check_login
router=APIRouter(prefix="/api/v1/auth",tags=["auth"])
@router.post("/register",response_model=UserResponse,status_code=201)
async def register(payload:UserRegisterRequest,session:DBSession):
    try: return await AuthService(session).register(payload.email,payload.password)
    except ConflictError as e: raise HTTPException(409,str(e))
@router.post("/login",response_model=TokenResponse)
async def login(payload:UserLoginRequest,request:Request,session:DBSession):
    allowed,retry=await check_login(request.client.host if request.client else "unknown")
    if not allowed: raise HTTPException(429,"Too many login attempts. Please try again later.",headers={"Retry-After":str(retry)})
    try: return TokenResponse(access_token=await AuthService(session).authenticate(payload.email,payload.password))
    except AuthenticationError as e: raise HTTPException(401,str(e),headers={"WWW-Authenticate":"Bearer"})
