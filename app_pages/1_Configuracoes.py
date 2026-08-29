"""Módulo 0 — Configurações do negócio.

Valores centrais usados no cálculo de preço de todas as receitas. Editáveis a
qualquer momento; mudanças valem só para novos cálculos (vendas já registradas
guardam seu próprio snapshot de custo, então nada do passado muda retroativamente).
"""
import streamlit as st

from auth import require_login
from db import ensure_business_config, get_session

require_login()

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
finally:
    session.close()
