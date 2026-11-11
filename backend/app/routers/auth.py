from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import create_token, current_user, hash_password, require_role, verify_password
from ..db import get_db
from ..models import User
from ..schemas import LoginIn, RegisterIn, TokenOut, UserOut

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/auth/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(username=body.username.strip().lower()).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Wrong username or password")
    return TokenOut(token=create_token(user), user=UserOut.model_validate(user))


@router.post("/auth/register", response_model=TokenOut)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    """Residents sign themselves up. Officers and workers are created by an admin."""
    username = body.username.strip().lower()
    if db.query(User).filter_by(username=username).first():
        raise HTTPException(409, "That username is taken")
    user = User(username=username, name=body.name.strip(), role="resident", password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    return TokenOut(token=create_token(user), user=UserOut.model_validate(user))


@router.get("/auth/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@router.get("/workers", response_model=list[UserOut])
def workers(db: Session = Depends(get_db), _: User = Depends(require_role("officer"))):
    return db.query(User).filter_by(role="worker").order_by(User.name).all()
