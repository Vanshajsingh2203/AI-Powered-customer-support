from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.database.session import get_db
from app.schemas.auth import UserRegister, UserResponse, LoginResponse, UserLogin, RefreshTokenRequest, RefreshTokenResponse
from app.services.auth_service import AuthService

router = APIRouter()

auth_service = AuthService()

@router.post('/register', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: AsyncSession=Depends(get_db)):
    try:
        user = await auth_service.register_user(db, user_data)
        
        await db.commit()
        await db.refresh(user)
        
        return user
    
    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code= status.HTTP_409_CONFLICT,
            detail = str(e)
        )
    
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )
        
@router.post('/login', response_model = LoginResponse, status_code=status.HTTP_200_OK)
async def login(login_data: UserLogin, db:AsyncSession = Depends(get_db)):
    try:
        result = await auth_service.login_user(db, login_data)
        
        await db.commit()
        await db.refresh(result["user"])
        
        return result
    
    except ValueError as exc:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )
        
@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    status_code=status.HTTP_200_OK,
)
async def refresh(
    token_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await auth_service.refresh_access_token(
            db=db,
            raw_refresh_token=token_data.refresh_token,
        )

        await db.commit()
        return result

    except ValueError as exc:
        if str(exc) == "Refresh token reuse detected":
            await db.commit()
        else:
            await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )

@router.post('/logout', status_code=status.HTTP_200_OK)
async def logout(
    token_data: RefreshTokenRequest,
    db: AsyncSession= Depends(get_db)
):
    try:
        await auth_service.logout_user(db, token_data.refresh_token)
        
        await db.commit()
        
        return {
            "Message": "Successfully logged out"
        }
        
    except ValueError as exc:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )