"""Módulo 0 — Configurações do negócio.

Valores centrais usados no cálculo de preço de todas as receitas. Editáveis a
qualquer momento; mudanças valem só para novos cálculos (vendas já registradas
guardam seu próprio snapshot de custo, então nada do passado muda retroativamente).
"""
import bcrypt
import streamlit as st

from db import ensure_business_config, get_session
from models import User

st.title("⚙️ Configurações do negócio")
st.caption(
    "Esses valores são usados no cálculo de preço de todas as receitas. "
    "Alterações valem para novos cálculos e não mudam vendas já registradas."
)

session = get_session()
try:
    config = ensure_business_config(session)

    st.subheader("Mão de obra")
    c1, c2 = st.columns(2)
    hours_per_day = c1.number_input(
        "Horas trabalhadas por dia", min_value=0.1, value=float(config.hours_per_day), step=0.5
    )
    days_per_week = c2.number_input(
        "Dias trabalhados por semana", min_value=0.1, value=float(config.days_per_week), step=0.5
    )
    monthly_salary = st.number_input(
        "Salário mensal desejado (R$)",
        min_value=0.0,
        value=float(config.monthly_salary),
        step=50.0,
        help="Usado para calcular o valor da sua hora de trabalho.",
    )

    st.subheader("Custos fixos")
    monthly_fixed_costs = st.number_input(
        "Custos fixos mensais (R$)",
        min_value=0.0,
        value=float(config.monthly_fixed_costs),
        step=10.0,
        help="Aluguel, gás, energia, etc. Rateado entre as receitas conforme o tempo de preparo.",
    )

    st.subheader("Preço de venda")
    c3, c4 = st.columns(2)
    tax_rate = c3.number_input(
        "Alíquota de impostos (%)", min_value=0.0, value=float(config.tax_rate * 100), step=0.5
    )
    commission_rate = c4.number_input(
        "Comissão (%)", min_value=0.0, value=float(config.commission_rate * 100), step=0.5
    )
    cento_discount = st.number_input(
        "Desconto para o cento (%)",
        min_value=0.0,
        max_value=100.0,
        value=float(config.cento_discount * 100),
        step=1.0,
        help="Aplicado sobre o preço de 100 unidades ao calcular o 'preço do cento'.",
    )

    st.subheader("Constantes da planilha")
    weeks_per_month = st.number_input(
        "Semanas por mês",
        min_value=0.1,
        value=float(config.weeks_per_month),
        step=0.01,
        help="Usada no cálculo do valor da hora e no rateio de custos fixos.",
    )
    fixed_cost_rate_constant = st.number_input(
        "Constante de rateio de custos fixos",
        value=float(config.fixed_cost_rate_constant),
        step=1.0,
        help=(
            "Herdada da planilha original — origem não identificada. Mantenha em 1400 "
            "a menos que saiba exatamente o que está mudando."
        ),
    )

    if st.button("💾 Salvar configurações", type="primary", use_container_width=True):
        if hours_per_day <= 0 or days_per_week <= 0 or weeks_per_month <= 0 or fixed_cost_rate_constant == 0:
            st.error("Os valores usados como divisor não podem ser zero ou negativos.")
        else:
            config.hours_per_day = hours_per_day
            config.days_per_week = days_per_week
            config.monthly_salary = monthly_salary
            config.monthly_fixed_costs = monthly_fixed_costs
            config.tax_rate = tax_rate / 100
            config.commission_rate = commission_rate / 100
            config.cento_discount = cento_discount / 100
            config.weeks_per_month = weeks_per_month
            config.fixed_cost_rate_constant = fixed_cost_rate_constant
            session.commit()
            st.success("Configurações salvas com sucesso.")

    st.divider()
    st.subheader("🔒 Alterar senha")
    st.caption("Troque a senha da sua conta de login. Não afeta nenhum outro dado do sistema.")

    with st.form("change_password_form", clear_on_submit=True):
        current_password = st.text_input("Senha atual", type="password")
        new_password = st.text_input("Nova senha", type="password")
        confirm_password = st.text_input("Confirmar nova senha", type="password")
        change_submitted = st.form_submit_button("Alterar senha", use_container_width=True)

    if change_submitted:
        username = st.session_state.get("logged_in_username", "")
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
finally:
    session.close()
