from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.infrastructure.adapters.database import get_session
from src.infrastructure.adapters.sql_models import UserModel
from src.infrastructure.api.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    create_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(data: RegisterRequest, session: Session = Depends(get_session)):
    try:
        existing = session.scalars(
            select(UserModel).where(UserModel.email == data.email)
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email ya registrado",
            )

        user = UserModel(
            name=data.name,
            email=data.email,
            password_hash=hash_password(data.password),
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        return TokenResponse(access_token=create_token(user.id, user.email))
    finally:
        session.close()


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, session: Session = Depends(get_session)):
    try:
        user = session.scalars(
            select(UserModel).where(UserModel.email == data.email)
        ).first()

        if not user or not user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
            )

        if not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
            )

        return TokenResponse(access_token=create_token(user.id, user.email))
    finally:
        session.close()
