from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User
from security import decode_access_token


def _get_user_from_token(authorization: str, db: Session) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header",
        )
    token = authorization.removeprefix("Bearer ").strip()

    try:
        username = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user


def get_current_user(
    authorization: str = Header(...), db: Session = Depends(get_db)
) -> User:
    """Require a valid token AND an active (non-withdrawn) account."""
    user = _get_user_from_token(authorization, db)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been withdrawn",
        )
    return user


def get_current_user_allow_withdrawn(
    authorization: str = Header(...), db: Session = Depends(get_db)
) -> User:
    """Require only a valid token; used by /auth/withdraw so it can report
    'already withdrawn' (400) instead of being preempted by the 403 that
    get_current_user would raise for an inactive account."""
    return _get_user_from_token(authorization, db)
