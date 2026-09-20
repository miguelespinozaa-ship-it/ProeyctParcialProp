from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from app.models import Rol


class RegisterRequest(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    telefono: Optional[str] = None
    rol: Rol


class RegisterResponse(BaseModel):
    id: int
    email: EmailStr
    rol: Rol
    token: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    rol: Rol
    restaurante_id: Optional[str] = None


class RefreshRequest(BaseModel):
    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str


class UsuarioOut(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    telefono: Optional[str] = None
    rol: Rol
    restaurante_id: Optional[str] = None
    fecha_registro: datetime

    class Config:
        from_attributes = True


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    telefono: Optional[str] = None


class DireccionCreate(BaseModel):
    calle: str
    ciudad: str
    referencia: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    es_principal: bool = False


class DireccionOut(DireccionCreate):
    id: int
    usuario_id: int

    class Config:
        from_attributes = True


class PaginatedUsuarios(BaseModel):
    items: list[UsuarioOut]
    page: int
    page_size: int
    total: int
    total_pages: int
