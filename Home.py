"""A.R Confeitaria — Sistema de gestão (Streamlit).

Ponto de entrada: configura a página, exige login e monta a navegação entre os módulos.
"""
from datetime import datetime, timedelta, timezone

import streamlit as st

from auth import logout_button, require_login
from db import ensure_business_config, get_session
from format_utils import format_currency, format_datetime, format_number
from models import Sale, CashEntry
from pwa import enable_pwa
from theme import apply_theme

st.set_page_config(page_title="A.R Confeitaria", page_icon="🧁", layout="centered")
apply_theme()
enable_pwa()

require_login()
logout_button()


def render_home():
    session = get_session()
    try:
        ensure_business_config(session)
        now = datetime.now(timezone.utc)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        active_entries = session.query(CashEntry).filter(CashEntry.status == "ATIVO").all()
        saldo_atual = sum(e.amount if e.type == "ENTRADA" else -e.amount for e in active_entries)

        sales_today = (
            session.query(Sale).filter(Sale.status == "ATIVA", Sale.sold_at >= day_start).all()
        )
        total_vendas_hoje = sum(s.quantity * s.unit_price_charged for s in sales_today)

        sales_month = (
            session.query(Sale).filter(Sale.status == "ATIVA", Sale.sold_at >= month_start).all()
        )
        product_counts: dict[str, float] = {}
        for s in sales_month:
            product_counts[s.product_name] = product_counts.get(s.product_name, 0) + s.quantity
        top_product = max(product_counts.items(), key=lambda kv: kv[1]) if product_counts else None

        recent_sales = (
            session.query(Sale)
            .filter(Sale.status == "ATIVA")
            .order_by(Sale.sold_at.desc())
            .limit(5)
            .all()
        )

        st.title("🧁 Início")
        st.caption(f"Resumo de hoje, {format_datetime(now)}")

        col1, col2 = st.columns(2)
        col1.metric("Caixa atual", format_currency(saldo_atual))
        col2.metric("Vendas de hoje", format_currency(total_vendas_hoje), f"{len(sales_today)} venda(s)")

        st.subheader("Produto mais vendido no mês")
        if top_product:
            st.info(f"**{top_product[0]}** ({format_number(top_product[1], 0)} un.)")
        else:
            st.info("Nenhuma venda este mês ainda.")

        st.subheader("Últimas vendas")
        if not recent_sales:
            st.caption("Nenhuma venda registrada ainda.")
        else:
            for s in recent_sales:
                c1, c2 = st.columns([3, 1])
                c1.write(f"**{s.product_name}**  \n:gray[{format_datetime(s.sold_at)}]")
                c2.write(format_currency(s.quantity * s.unit_price_charged))
    finally:
        session.close()


home_page = st.Page(render_home, title="Início", icon="🏠", default=True)
config_page = st.Page("app_pages/1_Configuracoes.py", title="Configurações", icon="⚙️")
insumos_page = st.Page("app_pages/2_Insumos.py", title="Insumos", icon="📦")
receitas_page = st.Page("app_pages/3_Receitas.py", title="Receitas", icon="📖")
vendas_page = st.Page("app_pages/4_Vendas.py", title="Vendas", icon="🛒")
caixa_page = st.Page("app_pages/5_Caixa.py", title="Caixa", icon="💰")
relatorios_page = st.Page("app_pages/6_Relatorios.py", title="Relatórios", icon="📊")
conta_page = st.Page("app_pages/7_Conta.py", title="Minha conta", icon="👤")

pg = st.navigation(
    [home_page, receitas_page, vendas_page, caixa_page, insumos_page, relatorios_page, config_page, conta_page]
)
pg.run()
