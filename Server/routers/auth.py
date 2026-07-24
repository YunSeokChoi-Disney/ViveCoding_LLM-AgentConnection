from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from deps import get_current_user_allow_withdrawn
from models import User
from schemas import (
    LoginRequest,
    SignupRequest,
    SignupResponse,
    TokenResponse,
    WithdrawResponse,
)
from security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == request.username).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    user = User(
        username=request.username,
        password_hash=hash_password(request.password),
        nickname=request.nickname,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return SignupResponse(
        id=user.id, username=user.username, nickname=user.nickname, message="Signup successful"
    )


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been withdrawn",
        )

    token = create_access_token(user.username)
    return TokenResponse(access_token=token, nickname=user.nickname)


@router.post("/withdraw", response_model=WithdrawResponse)
def withdraw(
    current_user: User = Depends(get_current_user_allow_withdrawn),
    db: Session = Depends(get_db),
):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account already withdrawn",
        )

    current_user.is_active = False
    current_user.deactivated_at = datetime.now(timezone.utc)
    db.add(current_user)
    db.commit()

    return WithdrawResponse(message="Account has been withdrawn")
