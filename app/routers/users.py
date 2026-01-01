"""Router de gestion des utilisateurs."""

import secrets
import string
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import hash_password
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, AuditLog

router = APIRouter()


class UserResponse(BaseModel):
    id: int
    username: str
    must_change_password: bool
    created_at: str
    last_login_at: str | None


class CreateUserRequest(BaseModel):
    username: str


class CreateUserResponse(BaseModel):
    id: int
    username: str
    generated_password: str
    must_change_password: bool


def generate_password(length: int = 12) -> str:
    """Génère un mot de passe aléatoire sécurisé."""
    alphabet = string.ascii_letters + string.digits + "!@#$%&*"
    password = "".join(secrets.choice(alphabet) for _ in range(length))
    return password


@router.get("/", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Liste tous les utilisateurs."""
    users = db.query(User).order_by(User.username).all()

    return [
        UserResponse(
            id=u.id,
            username=u.username,
            must_change_password=u.must_change_password,
            created_at=u.created_at.isoformat(),
            last_login_at=u.last_login_at.isoformat() if u.last_login_at else None,
        )
        for u in users
    ]


@router.post(
    "/", response_model=CreateUserResponse, status_code=status.HTTP_201_CREATED
)
def create_user(
    request: CreateUserRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Crée un nouvel utilisateur avec un mot de passe généré automatiquement.
    Le mot de passe devra être changé à la première connexion.
    """
    # Vérifier si l'utilisateur existe déjà
    existing = db.query(User).filter(User.username == request.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"L'utilisateur '{request.username}' existe déjà",
        )

    # Générer un mot de passe aléatoire
    generated_password = generate_password()

    # Créer l'utilisateur
    new_user = User(
        username=request.username,
        password_hash=hash_password(generated_password),
        must_change_password=True,  # Obligatoire à la première connexion
        created_at=datetime.utcnow(),
    )

    db.add(new_user)

    # Logger l'action
    audit = AuditLog(
        user_id=current_user.id,
        action="create_user",
        details_json={"created_username": request.username},
    )
    db.add(audit)

    db.commit()
    db.refresh(new_user)

    return CreateUserResponse(
        id=new_user.id,
        username=new_user.username,
        generated_password=generated_password,
        must_change_password=True,
    )


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Supprime un utilisateur.
    Un utilisateur ne peut pas se supprimer lui-même.
    """
    # Vérifier qu'on ne se supprime pas soi-même
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous ne pouvez pas supprimer votre propre compte",
        )

    # Récupérer l'utilisateur à supprimer
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Utilisateur avec l'ID {user_id} introuvable",
        )

    # Logger l'action avant suppression
    audit = AuditLog(
        user_id=current_user.id,
        action="delete_user",
        details_json={"deleted_username": user.username, "deleted_user_id": user_id},
    )
    db.add(audit)

    # Supprimer l'utilisateur
    db.delete(user)
    db.commit()

    return {"message": f"Utilisateur '{user.username}' supprimé avec succès"}
