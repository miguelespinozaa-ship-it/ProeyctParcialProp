import enum

from sqlalchemy import DECIMAL, Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base


class Rol(str, enum.Enum):
    customer = "customer"
    delivery = "delivery"
    admin = "admin"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    telefono = Column(String(30))
    rol = Column(Enum(Rol), nullable=False, index=True)
    restaurante_id = Column(String(50), nullable=True)
    fecha_registro = Column(DateTime, server_default=func.now())

    direcciones = relationship("Direccion", back_populates="usuario", cascade="all, delete-orphan")


class Direccion(Base):
    __tablename__ = "direcciones"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    calle = Column(String(255), nullable=False)
    ciudad = Column(String(100), nullable=False)
    referencia = Column(String(255))
    lat = Column(DECIMAL(10, 7))
    lng = Column(DECIMAL(10, 7))
    es_principal = Column(Boolean, default=False)

    usuario = relationship("Usuario", back_populates="direcciones")
