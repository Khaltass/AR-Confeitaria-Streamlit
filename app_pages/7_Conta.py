"""Configurações do usuário: trocar senha e zerar o aplicativo.

Separado das Configurações do negócio (Módulo 0) porque são ajustes da conta,
não da precificação.
"""
import bcrypt
import streamlit as st

from auth import require_login
from db import get_session
from models import (
    BusinessConfig,
    CashEntry,
    ExpenseCategory,
    Ingredient,
    IngredientPriceHistory,
    Recipe,
    RecipeIngredient,
    Sale,
    User,
)

require_login()

st.title("👤 Configurações do usuário")

session = get_session()
try:
    username = st.session_state.get("logged_in_username", "")

    st.subheader("🔒 Alterar senha")
    st.caption("Troque a senha da sua conta de login. Não afeta nenhum outro dado do sistema.")

    with st.form("change_password_form", clear_on_submit=True):
        current_password = st.text_input("Senha atual", type="password")
        new_password = st.text_input("Nova senha", type="password")
        confirm_password = st.text_input("Confirmar nova senha", type="password")
        change_submitted = st.form_submit_button("Alterar senha", use_container_width=True)

    if change_submitted:
        user = session.query(User).filter(User.username == username).first()

        if user is None or not bcrypt.checkpw(
            current_password.encode("utf-8"), user.password_hash.encode("utf-8")
        ):
            st.error("Senha atual incorreta.")
        elif len(new_password) < 8:
            st.error("A nova senha deve ter pelo menos 8 caracteres.")
        elif new_password != confirm_password:
            st.error("As senhas não coincidem.")
        elif new_password == current_password:
            st.error("A nova senha precisa ser diferente da atual.")
        else:
            user.password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            session.commit()
            st.toast("Senha alterada com sucesso.", icon="✅")

    st.divider()
    st.subheader("🗑️ Zerar aplicativo")
    st.error(
        "Isso apaga **permanentemente** todos os insumos, receitas, vendas, lançamentos de "
        "caixa e categorias de despesa, e restaura as configurações do negócio (Módulo 0) para "
        "os valores padrão. **Não pode ser desfeito.** O seu login continua o mesmo."
    )

    with st.form("reset_app_form", clear_on_submit=True):
        confirm_phrase = st.text_input('Digite "APAGAR TUDO" para confirmar')
        confirm_password = st.text_input("Sua senha atual", type="password")
        reset_submitted = st.form_submit_button(
            "🗑️ Apagar todos os dados permanentemente", use_container_width=True
        )

    if reset_submitted:
        user = session.query(User).filter(User.username == username).first()

        if confirm_phrase.strip().upper() != "APAGAR TUDO":
            st.error('Digite exatamente "APAGAR TUDO" para confirmar.')
        elif user is None or not bcrypt.checkpw(
            confirm_password.encode("utf-8"), user.password_hash.encode("utf-8")
        ):
            st.error("Senha incorreta.")
        else:
            # Ordem respeita as chaves estrangeiras (filhos antes dos pais).
            session.query(CashEntry).delete()
            session.query(Sale).delete()
            session.query(RecipeIngredient).delete()
            session.query(Recipe).delete()
            session.query(IngredientPriceHistory).delete()
            session.query(Ingredient).delete()
            session.query(ExpenseCategory).delete()
            session.query(BusinessConfig).delete()
            session.commit()
            st.toast("Aplicativo zerado com sucesso.", icon="✅")
            st.rerun()
finally:
    session.close()
