"""Módulo 4 — Fluxo de Caixa."""
from datetime import datetime, timedelta, timezone

import streamlit as st

from auth import require_login
from db import get_session
from format_utils import format_currency, format_datetime
from models import CashEntry, ExpenseCategory

require_login()

st.title("💰 Fluxo de caixa")
st.caption("Entradas e saídas, com saldo por período.")

PERIODS = {"Hoje": "dia", "Esta semana": "semana", "Este mês": "mes", "Este ano": "ano", "Tudo": "tudo"}


def period_range(period_key: str):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period_key == "dia":
        return today_start, today_start + timedelta(days=1)
    if period_key == "semana":
        # weekday(): segunda=0 ... domingo=6. Semana começando no domingo, como no app Next.js.
        start = today_start - timedelta(days=(today_start.weekday() + 1) % 7)
        return start, start + timedelta(days=7)
    if period_key == "mes":
        start = today_start.replace(day=1)
        next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        return start, next_month
    if period_key == "ano":
        start = today_start.replace(month=1, day=1)
        return start, start.replace(year=start.year + 1)
    return None, None


session = get_session()
try:
    active_entries = session.query(CashEntry).filter(CashEntry.status == "ATIVO").all()
    saldo_atual = sum(e.amount if e.type == "ENTRADA" else -e.amount for e in active_entries)

    categories = session.query(ExpenseCategory).order_by(ExpenseCategory.name).all()

    st.subheader("Novo lançamento")
    entry_type_label = st.radio("Tipo", ["Entrada", "Saída"], horizontal=True, index=1)
    entry_type = "ENTRADA" if entry_type_label == "Entrada" else "SAIDA"

    description = st.text_input("Descrição", placeholder="Ex: Compra de insumos" if entry_type == "SAIDA" else "Ex: Receita extra")
    c1, c2 = st.columns(2)
    amount = c1.number_input("Valor (R$)", min_value=0.0, step=1.0)
    entry_date = c2.date_input("Data", value=datetime.now().date(), format="DD/MM/YYYY")

    category_id = None
    if entry_type == "SAIDA":
        cat_names = ["Sem categoria"] + [c.name for c in categories]
        chosen_cat = st.selectbox("Categoria (opcional)", cat_names)
        if chosen_cat != "Sem categoria":
            category_id = next(c.id for c in categories if c.name == chosen_cat)

    if st.button("Adicionar lançamento", type="primary", use_container_width=True):
        if amount <= 0:
            st.error("O valor deve ser maior que zero.")
        elif not description.strip():
            st.error("Descreva o lançamento.")
        else:
            session.add(
                CashEntry(
                    type=entry_type,
                    amount=amount,
                    description=description.strip(),
                    date=datetime.combine(entry_date, datetime.now().time()).replace(tzinfo=timezone.utc),
                    category_id=category_id,
                )
            )
            session.commit()
            st.toast("Lançamento salvo com sucesso.", icon="✅")
            st.rerun()

    with st.expander("Gerenciar categorias de despesa"):
        if categories:
            st.write(", ".join(c.name for c in categories))
        new_cat = st.text_input("Nova categoria", key="new_category_name")
        if st.button("Adicionar categoria"):
            if new_cat.strip() and not any(c.name == new_cat.strip() for c in categories):
                session.add(ExpenseCategory(name=new_cat.strip()))
                session.commit()
                st.rerun()

    st.divider()

    col1, col2 = st.columns(2)
    col1.metric("Saldo atual", format_currency(saldo_atual))

    period_label = st.radio("Período", list(PERIODS.keys()), horizontal=True, index=2)
    period_key = PERIODS[period_label]
    start, end = period_range(period_key)

    query = session.query(CashEntry)
    if start and end:
        query = query.filter(CashEntry.date >= start, CashEntry.date < end)
    entries = query.order_by(CashEntry.date.desc()).all()

    saldo_periodo = sum(e.amount if e.type == "ENTRADA" else -e.amount for e in entries if e.status == "ATIVO")
    col2.metric("Saldo no período", format_currency(saldo_periodo))

    if not entries:
        st.caption("Nenhum lançamento neste período.")
    for entry in entries:
        c1, c2, c3 = st.columns([3, 2, 1])
        tags = []
        if entry.status == "ESTORNADO":
            tags.append("estornado")
        if entry.category:
            tags.append(entry.category.name)
        tag_text = f"  ·  {' · '.join(tags)}" if tags else ""
        c1.write(f"**{entry.description}**{tag_text}  \n:gray[{format_datetime(entry.date)}]")
        sign = "+" if entry.type == "ENTRADA" else "-"
        value_text = f"{sign}{format_currency(entry.amount)}"
        c2.write(f"~~{value_text}~~" if entry.status == "ESTORNADO" else f"**{value_text}**")
        if entry.status == "ATIVO" and not entry.sale_id:
            if c3.button("Estornar", key=f"rev_{entry.id}"):
                st.session_state[f"confirm_rev_{entry.id}"] = True
        if st.session_state.get(f"confirm_rev_{entry.id}"):
            st.warning("Estornar este lançamento? Um lançamento contrário será criado e este ficará marcado como estornado.")
            cc1, cc2 = st.columns(2)
            if cc1.button("Sim, estornar", key=f"rev_yes_{entry.id}", type="primary"):
                entry.status = "ESTORNADO"
                session.add(
                    CashEntry(
                        type="SAIDA" if entry.type == "ENTRADA" else "ENTRADA",
                        amount=entry.amount,
                        description=f"Estorno: {entry.description}",
                        date=datetime.now(timezone.utc),
                        category_id=entry.category_id,
                        reversal_of_id=entry.id,
                    )
                )
                session.commit()
                del st.session_state[f"confirm_rev_{entry.id}"]
                st.rerun()
            if cc2.button("Não", key=f"rev_no_{entry.id}"):
                del st.session_state[f"confirm_rev_{entry.id}"]
                st.rerun()
finally:
    session.close()
