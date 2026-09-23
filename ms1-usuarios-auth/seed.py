"""Carga masiva de usuarios (>= 20,000 registros) - MS1. Correr una sola vez: `python seed.py`"""

import random

from faker import Faker
from passlib.hash import bcrypt

from app.db import Base, SessionLocal, engine
from app.models import Direccion, Rol, Usuario

fake = Faker("es_MX")

TOTAL_USUARIOS = 20_000
PASSWORD_HASH = bcrypt.hash("password123")


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        usuarios = []
        for i in range(TOTAL_USUARIOS):
            rol = random.choices([Rol.customer, Rol.delivery], weights=[0.85, 0.15])[0]
            usuarios.append(
                Usuario(
                    nombre=fake.name(),
                    email=f"user{i}_{fake.user_name()}@demo.com",
                    password_hash=PASSWORD_HASH,
                    telefono=fake.phone_number()[:30],
                    rol=rol,
                )
            )
        db.bulk_save_objects(usuarios, return_defaults=True)
        db.commit()

        customers = db.query(Usuario).filter(Usuario.rol == Rol.customer).all()
        direcciones = [
            Direccion(
                usuario_id=u.id,
                calle=fake.street_address(),
                ciudad=fake.city(),
                referencia=fake.sentence(nb_words=4),
                es_principal=True,
            )
            for u in customers
        ]
        db.bulk_save_objects(direcciones)
        db.commit()
        print(f"Seed completo: {len(usuarios)} usuarios, {len(direcciones)} direcciones.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
