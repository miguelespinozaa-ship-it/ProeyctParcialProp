import math
from typing import Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user, require_admin
from app.models import Rol, Usuario
from app.schemas import PaginatedUsuarios, UsuarioOut, UsuarioUpdate

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


MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20


@router.get("/users", response_model=Union[PaginatedUsuarios, list[UsuarioOut]])
def list_users(
    response: Response,
    rol: Optional[str] = None,
    ids: Optional[str] = None,
    page: Optional[int] = Query(None, ge=1, description="Activa el paginado (desde 1). Sin page/page_size devuelve todo."),
    page_size: Optional[int] = Query(None, ge=1, description=f"Tamaño de página (por defecto {DEFAULT_PAGE_SIZE}, máximo {MAX_PAGE_SIZE})"),
    db: Session = Depends(get_db),
):
    # También lo consumen MS3/MS4 internamente; sin JWT propio, a diferencia del resto de rutas.
    query = db.query(Usuario)
    if rol is not None:
        query = query.filter(Usuario.rol == rol)
    if ids is not None:
        id_list = [int(x) for x in ids.split(",") if x.strip()]
        query = query.filter(Usuario.id.in_(id_list))
    query = query.order_by(Usuario.id)

    if page is None and page_size is None:
        users = query.all()
        response.headers["X-Total-Count"] = str(len(users))
        return users

    page = page or 1
    size = min(page_size or DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE)
    total = query.count()
    rows = query.offset((page - 1) * size).limit(size).all()
    response.headers["X-Total-Count"] = str(total)
    return PaginatedUsuarios(
        items=[UsuarioOut.model_validate(r) for r in rows],
        page=page,
        page_size=size,
        total=total,
        total_pages=math.ceil(total / size),
    )


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
