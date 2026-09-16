from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import Direccion, Usuario
from app.schemas import DireccionCreate, DireccionOut

router = APIRouter(prefix="/api/v1", tags=["addresses"])


def _get_owned_address(address_id: int, current_user: Usuario, db: Session) -> Direccion:
    direccion = db.query(Direccion).filter(Direccion.id == address_id).first()
    if direccion is None:
        raise HTTPException(status_code=404, detail="Dirección no encontrada")
    if direccion.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado")
    return direccion


@router.get("/users/{user_id}/addresses", response_model=list[DireccionOut])
def list_addresses(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    return db.query(Direccion).filter(Direccion.usuario_id == user_id).all()


@router.post("/users/{user_id}/addresses", response_model=DireccionOut, status_code=201)
def create_address(
    user_id: int,
    payload: DireccionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    direccion = Direccion(usuario_id=user_id, **payload.model_dump())
    db.add(direccion)
    db.commit()
    db.refresh(direccion)
    return direccion


@router.put("/addresses/{address_id}", response_model=DireccionOut)
def update_address(
    address_id: int,
    payload: DireccionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    direccion = _get_owned_address(address_id, current_user, db)
    for field, value in payload.model_dump().items():
        setattr(direccion, field, value)
    db.commit()
    db.refresh(direccion)
    return direccion


@router.delete("/addresses/{address_id}", status_code=204)
def delete_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    direccion = _get_owned_address(address_id, current_user, db)
    db.delete(direccion)
    db.commit()
