from fastapi import APIRouter, Depends, HTTPException
from jose import JWTError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Rol, Usuario
from app.schemas import (
    AccessTokenResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from app.security import create_access_token, decode_token, hash_password, verify_password

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if payload.rol == Rol.admin:
        raise HTTPException(status_code=400, detail="No se permite registrar rol=admin")

    if db.query(Usuario).filter(Usuario.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email ya registrado")

    usuario = Usuario(
        nombre=payload.nombre,
        email=payload.email,
        password_hash=hash_password(payload.password),
        telefono=payload.telefono,
        rol=payload.rol,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    token = create_access_token({"sub": str(usuario.id), "rol": usuario.rol.value})
    return RegisterResponse(id=usuario.id, email=usuario.email, rol=usuario.rol, token=token)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == payload.email).first()
    if usuario is None or not verify_password(payload.password, usuario.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    token_data = {"sub": str(usuario.id), "rol": usuario.rol.value}
    restaurante_id = None
    if usuario.rol == Rol.admin:
        token_data["restaurante_id"] = usuario.restaurante_id
        restaurante_id = usuario.restaurante_id

    access_token = create_access_token(token_data)
    return TokenResponse(access_token=access_token, rol=usuario.rol, restaurante_id=restaurante_id)


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(payload: RefreshRequest):
    try:
        decoded = decode_token(payload.refresh_token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    new_token = create_access_token({"sub": decoded["sub"], "rol": decoded["rol"]})
    return AccessTokenResponse(access_token=new_token)
