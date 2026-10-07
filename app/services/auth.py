from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.users import UserRepository
class AuthService:
    def __init__(self,session): self.repo=UserRepository(session); self.session=session
    async def register(self,email,password):
        email=email.lower().strip()
        if await self.repo.get_by_email(email): raise ConflictError("Email already registered")
        user=User(email=email,password_hash=hash_password(password)); await self.repo.create(user); await self.session.commit(); return user
    async def authenticate(self,email,password):
        user=await self.repo.get_by_email(email.lower().strip())
        if not user or not verify_password(password,user.password_hash): raise AuthenticationError("Invalid credentials")
        return create_access_token(user.id)
