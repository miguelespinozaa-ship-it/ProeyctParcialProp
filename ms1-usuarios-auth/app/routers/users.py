from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user, require_admin
from app.models import Rol, Usuario
from app.schemas import UsuarioOut, UsuarioUpdate

router = APIRouter(prefix="/api/v1", tags=["users"])


@router.get("/users/{user_id}", response_model=UsuarioOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if current_user.id != user_id and current_user.rol != Rol.admin:
        raise HTTPException(status_code=403, detail="No autorizado")
    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


@router.put("/users/{user_id}", response_model=UsuarioOut)
def update_user(
    user_id: int,
    payload: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if payload.nombre is not None:
        usuario.nombre = payload.nombre
    if payload.telefono is not None:
        usuario.telefono = payload.telefono
    db.commit()
    db.refresh(usuario)
    return usuario


@router.get("/users", response_model=list[UsuarioOut])
def list_users(
    rol: Optional[str] = None,
    ids: Optional[str] = None,
    db: Session = Depends(get_db),
):
    # Nota: endpoint también consumido internamente por MS3/MS4 (red docker privada),
    # por eso no exige JWT propio como el resto — ver 00-mapa-conexiones.md.
    query = db.query(Usuario)
    if rol is not None:
        query = query.filter(Usuario.rol == rol)
    if ids is not None:
        id_list = [int(x) for x in ids.split(",") if x.strip()]
        query = query.filter(Usuario.id.in_(id_list))
    return query.all()


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
):
    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.delete(usuario)
    db.commit()
