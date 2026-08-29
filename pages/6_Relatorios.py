"""Módulo 5 — Histórico e Relatórios."""
import io
from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st

from db import get_session
from format_utils import format_currency, format_datetime, format_number
from models import PAYMENT_LABELS, CashEntry, Sale

st.title("📊 Relatórios")
st.caption("Histórico completo, gráficos e exportação.")


def csv_safe(value: str) -> str:
    """Evita CSV/Formula Injection: neutraliza células que comecem com = + - @ no Excel."""
    text = str(value or "")
    if text[:1] in ("=", "+", "-", "@", "\t"):
        return "'" + text
    return text


session = get_session()
try:
    today = datetime.now(timezone.utc).date()
    month_start = today.replace(day=1)

    c1, c2 = st.columns(2)
    start_date = c1.date_input("De", value=month_start, format="DD/MM/YYYY")
    end_date = c2.date_input("Até", value=today, format="DD/MM/YYYY")

    start_dt = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_dt = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)

    sales = (
        session.query(Sale)
        .filter(Sale.status == "ATIVA", Sale.sold_at >= start_dt, Sale.sold_at <= end_dt)
        .all()
    )
    all_cash_entries = session.query(CashEntry).filter(CashEntry.status == "ATIVO").order_by(CashEntry.date.asc()).all()

    total_faturado = sum(s.quantity * s.unit_price_charged for s in sales)
    total_custo = sum(s.quantity * s.unit_cost_snapshot for s in sales)
    lucro_total = total_faturado - total_custo
    total_unidades = sum(s.quantity for s in sales)

    k1, k2, k3 = st.columns(3)
    k1.metric("Faturado", format_currency(total_faturado))
    k2.metric("Lucro", format_currency(lucro_total))
    k3.metric("Unidades vendidas", format_number(total_unidades, 0))

    # ---- Exportação CSV ----
    st.subheader("Exportar dados")
    ce1, ce2 = st.columns(2)

    sales_rows = [
        {
            "Data": format_datetime(s.sold_at),
            "Produto": csv_safe(s.product_name),
            "Quantidade": s.quantity,
            "Preço unitário": s.unit_price_charged,
            "Total": s.quantity * s.unit_price_charged,
            "Custo unitário": s.unit_cost_snapshot,
            "Forma de pagamento": PAYMENT_LABELS.get(s.payment_method, s.payment_method),
            "Cliente": csv_safe(s.customer or ""),
            "Status": "Ativa" if s.status == "ATIVA" else "Cancelada",
            "Observação": csv_safe(s.note or ""),
        }
        for s in session.query(Sale).filter(Sale.sold_at >= start_dt, Sale.sold_at <= end_dt).order_by(Sale.sold_at).all()
    ]
    sales_csv = pd.DataFrame(sales_rows).to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
    ce1.download_button("Exportar vendas (CSV)", sales_csv, "vendas.csv", "text/csv", use_container_width=True)

    cash_rows = [
        {
            "Data": format_datetime(e.date),
            "Tipo": "Entrada" if e.type == "ENTRADA" else "Saída",
            "Descrição": csv_safe(e.description),
            "Categoria": csv_safe(e.category.name if e.category else ""),
            "Valor": e.amount,
            "Status": "Ativo" if e.status == "ATIVO" else "Estornado",
        }
        for e in session.query(CashEntry).filter(CashEntry.date >= start_dt, CashEntry.date <= end_dt).order_by(CashEntry.date).all()
    ]
    cash_csv = pd.DataFrame(cash_rows).to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
    ce2.download_button("Exportar caixa (CSV)", cash_csv, "caixa.csv", "text/csv", use_container_width=True)

    # ---- Evolução do caixa ----
    st.subheader("Evolução do caixa")
    if all_cash_entries:
        daily_net: dict[str, float] = {}
        for e in all_cash_entries:
            key = e.date.strftime("%d/%m/%Y")
            delta = e.amount if e.type == "ENTRADA" else -e.amount
            daily_net[key] = daily_net.get(key, 0) + delta
        running = 0.0
        chart_rows = []
        for date_key, delta in daily_net.items():
            running += delta
            chart_rows.append({"Data": date_key, "Saldo": running})
        chart_df = pd.DataFrame(chart_rows).set_index("Data").tail(60)
        st.line_chart(chart_df)
    else:
        st.caption("Sem dados suficientes para o gráfico.")

    # ---- Ranking de produtos ----
    st.subheader("Produtos mais vendidos (período filtrado)")
    by_product: dict[str, dict] = {}
    for s in sales:
        agg = by_product.setdefault(s.product_name, {"quantity": 0.0, "revenue": 0.0, "cost": 0.0})
        agg["quantity"] += s.quantity
        agg["revenue"] += s.quantity * s.unit_price_charged
        agg["cost"] += s.quantity * s.unit_cost_snapshot

    if not by_product:
        st.caption("Nenhuma venda no período selecionado.")
    else:
        ranking = sorted(by_product.items(), key=lambda kv: kv[1]["quantity"], reverse=True)[:10]
        for idx, (name, agg) in enumerate(ranking, start=1):
            c1, c2 = st.columns([4, 1])
            c1.write(f"{idx}. {name}")
            c2.write(f"{format_number(agg['quantity'], 0)} un.")

        # ---- Lucro por produto ----
        st.subheader("Lucro por produto (período filtrado)")
        profit_rows = [
            {
                "Produto": name,
                "Qtd.": format_number(agg["quantity"], 0),
                "Faturado": format_currency(agg["revenue"]),
                "Custo": format_currency(agg["cost"]),
                "Lucro": format_currency(agg["revenue"] - agg["cost"]),
            }
            for name, agg in sorted(by_product.items(), key=lambda kv: kv[1]["revenue"] - kv[1]["cost"], reverse=True)
        ]
        st.dataframe(pd.DataFrame(profit_rows), use_container_width=True, hide_index=True)
finally:
    session.close()
