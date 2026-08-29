"""Troca a senha de login sem apagar nenhum outro dado (vendas, insumos, config, etc.).

Rode com DATABASE_URL apontando para o banco desejado. Se NEW_LOGIN_PASSWORD não for
definida, uma senha aleatória forte é gerada e impressa uma única vez no terminal --
anote-a na hora, ela não fica salva em nenhum arquivo.

    $env:DATABASE_URL="postgresql://..."
    python rotate_login_password.py [usuario]
"""
import os
import secrets
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, User


def get_engine():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("Defina DATABASE_URL antes de rodar este script.")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return create_engine(url, connect_args={"sslmode": "require"})


def generate_password() -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789"
    return "".join(secrets.choice(alphabet) for _ in range(14))


def main():
    username = (sys.argv[1] if len(sys.argv) > 1 else "amanda").strip().lower()
    new_password = os.environ.get("NEW_LOGIN_PASSWORD") or generate_password()

    engine = get_engine()
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    user = session.query(User).filter(User.username == username).first()
    if user is None:
        session.close()
        raise SystemExit(f"Usuário '{username}' não encontrado -- nada foi alterado.")

    user.password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    session.commit()
    session.close()

    print(f"Senha do usuário '{username}' atualizada com sucesso.")
    print(f"Nova senha: {new_password}")
    print("Guarde-a agora -- ela não é salva em nenhum arquivo ou log.")


if __name__ == "__main__":
    main()
