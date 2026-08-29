"""Conexão com o banco (SQLite local ou Postgres/Supabase) — mesmo padrão do outro app.

Se a secret/variável de ambiente DATABASE_URL estiver definida, conecta no Postgres.
Caso contrário, cai no SQLite local em data/app.db. O resto do código usa só a
sessão do SQLAlchemy, então nenhuma outra parte do app precisa saber qual banco é.
"""
import os
from pathlib import Path

import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from models import Base, BusinessConfig

DATA_DIR = Path(__file__).parent / "data"
SQLITE_PATH = DATA_DIR / "app.db"


def _get_database_url() -> str | None:
    try:
        if "DATABASE_URL" in st.secrets:
            return st.secrets["DATABASE_URL"]
    except Exception:
        pass
    return os.environ.get("DATABASE_URL")


@st.cache_resource
def get_engine():
    url = _get_database_url()
    if url:
        # Supabase/Postgres: normaliza o prefixo aceito pelo SQLAlchemy e força SSL.
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        connect_args = {"sslmode": "require"} if "sslmode" not in url else {}
        engine = create_engine(url, pool_pre_ping=True, connect_args=connect_args)
    else:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        engine = create_engine(f"sqlite:///{SQLITE_PATH}", connect_args={"check_same_thread": False})

    Base.metadata.create_all(engine)
    return engine


@st.cache_resource
def get_session_factory():
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_session() -> Session:
    return get_session_factory()()


def using_postgres() -> bool:
    return _get_database_url() is not None


def ensure_business_config(session: Session) -> BusinessConfig:
    """Garante que sempre exista uma linha de configurações (cria com os padrões se não existir)."""
    config = session.query(BusinessConfig).first()
    if config is None:
        config = BusinessConfig()
        session.add(config)
        session.commit()
        session.refresh(config)
    return config
