"""Router d'authentification."""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.auth import authenticate_user, create_access_token, get_current_user, hash_password
from app.models import User, AuditLog

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    must_change_password: bool


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authentifie un utilisateur et retourne un token JWT.
    """
    user = authenticate_user(db, request.username, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Créer le token
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(hours=8)
    )
    
    # Mettre à jour last_login_at
    from datetime import datetime
    user.last_login_at = datetime.utcnow()
    
    # Logger l'action
    audit = AuditLog(
        user_id=user.id,
        action="login",
        details_json={"username": user.username}
    )
    db.add(audit)
    db.commit()
    
    return LoginResponse(
        access_token=access_token,
        must_change_password=user.must_change_password
    )


@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Change le mot de passe de l'utilisateur courant."""
    user = get_current_user(db, token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide"
        )
    
    # Vérifier l'ancien mot de passe
    from app.auth import verify_password
    if not verify_password(request.old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ancien mot de passe incorrect"
        )
    
    # Changer le mot de passe
    user.password_hash = hash_password(request.new_password)
    user.must_change_password = False
    
    # Logger l'action
    audit = AuditLog(
        user_id=user.id,
        action="change_password",
        details_json={"username": user.username}
    )
    db.add(audit)
    db.commit()
    
    return {"message": "Mot de passe changé avec succès"}


@router.post("/logout")
def logout(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Déconnecte l'utilisateur (côté client)."""
    user = get_current_user(db, token)
    
    if user:
        # Logger l'action
        audit = AuditLog(
            user_id=user.id,
            action="logout",
            details_json={"username": user.username}
        )
        db.add(audit)
        db.commit()
    
    return {"message": "Déconnexion réussie"}


@router.get("/me")
def get_current_user_info(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Retourne les informations de l'utilisateur courant."""
    user = get_current_user(db, token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide"
        )
    
    return {
        "id": user.id,
        "username": user.username,
        "must_change_password": user.must_change_password,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None
    }
