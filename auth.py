"""Login simples por usuário/senha (Requisito não-funcional: uso pessoal, sem complexidade)."""
import bcrypt
import streamlit as st

from db import get_session
from models import User


def is_logged_in() -> bool:
    return bool(st.session_state.get("logged_in_username"))


def require_login():
    """Bloqueia o resto da página até o login ser feito. Chame no topo de cada página."""
    if is_logged_in():
        return

    st.title("🧁 A.R Confeitaria")
    st.caption("Sistema de gestão")

    with st.form("login_form"):
        username = st.text_input("Usuário", placeholder="amanda")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar", use_container_width=True)

    if submitted:
        session = get_session()
        try:
            user = (
                session.query(User)
                .filter(User.username == username.strip().lower())
                .first()
            )
            valid = user is not None and bcrypt.checkpw(
                password.encode("utf-8"), user.password_hash.encode("utf-8")
            )
        finally:
            session.close()

        if valid:
            st.session_state["logged_in_username"] = username.strip().lower()
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")

    st.stop()


def logout_button():
    with st.sidebar:
        st.caption(f"Logada como **{st.session_state.get('logged_in_username', '')}**")
        if st.button("Sair", use_container_width=True):
            st.session_state.clear()
            st.rerun()
