"""Módulo 3 — Lançamento de Vendas."""
from datetime import datetime, timezone

import streamlit as st

from auth import require_login
from db import ensure_business_config, get_session
from format_utils import format_currency, format_datetime
from models import PAYMENT_LABELS, PAYMENT_METHODS, CashEntry, Recipe, Sale
from pricing import calculate_recipe_pricing, config_to_pricing_input, recipe_to_pricing_input

require_login()

st.title("🛒 Vendas")
st.caption("Registre cada venda do dia a dia.")

session = get_session()
try:
    config = ensure_business_config(session)
    pricing_config = config_to_pricing_input(config)
    recipes = session.query(Recipe).filter(Recipe.active == True).order_by(Recipe.name).all()  # noqa: E712

    recipe_options = {"Item avulso (fora do cadastro)": None}
    recipe_prices = {}
    for r in recipes:
        breakdown = calculate_recipe_pricing(recipe_to_pricing_input(r), pricing_config)
        label = f"{r.name} — sugerido {format_currency(breakdown.preco_unidade)}"
        recipe_options[label] = r.id
        recipe_prices[r.id] = breakdown

    st.subheader("Nova venda")
    choice = st.selectbox("Produto", list(recipe_options.keys()), key="sale_product_choice")
    recipe_id = recipe_options[choice]

    manual_name = ""
    if recipe_id is None:
        manual_name = st.text_input("Nome do item", placeholder="Ex: Encomenda especial")

    default_price = recipe_prices[recipe_id].preco_unidade if recipe_id else 0.0

    c1, c2 = st.columns(2)
    quantity = c1.number_input("Quantidade", min_value=0.01, value=1.0, step=1.0)
    unit_price_charged = c2.number_input(
        "Preço praticado (R$)", min_value=0.0, value=round(default_price, 2), step=0.5,
        help="Pré-preenchido com o preço sugerido, pode ajustar." if recipe_id else None,
    )

    c3, c4 = st.columns(2)
    payment_label = c3.selectbox("Forma de pagamento", [PAYMENT_LABELS[p] for p in PAYMENT_METHODS])
    payment_method = PAYMENT_METHODS[[PAYMENT_LABELS[p] for p in PAYMENT_METHODS].index(payment_label)]
    sold_at_date = c4.date_input("Data", value=datetime.now().date(), format="DD/MM/YYYY")

    c5, c6 = st.columns(2)
    customer = c5.text_input("Cliente (opcional)")
    note = c6.text_input("Observação (opcional)")

    total = quantity * unit_price_charged
    st.info(f"**Total da venda: {format_currency(total)}**")

    if st.button("Registrar venda", type="primary", use_container_width=True):
        product_name = manual_name.strip() if recipe_id is None else None
        unit_cost_snapshot = 0.0
        suggested_unit_price = None

        if recipe_id:
            recipe = session.query(Recipe).get(recipe_id)
            product_name = recipe.name
            breakdown = recipe_prices[recipe_id]
            unit_cost_snapshot = breakdown.custo_producao_unidade
            suggested_unit_price = breakdown.preco_unidade

        if quantity <= 0:
            st.error("A quantidade deve ser maior que zero.")
        elif not product_name:
            st.error("Selecione um produto ou informe o nome do item avulso.")
        else:
            sold_at = datetime.combine(sold_at_date, datetime.now().time()).replace(tzinfo=timezone.utc)
            sale = Sale(
                recipe_id=recipe_id,
                product_name=product_name,
                quantity=quantity,
                unit_price_charged=unit_price_charged,
                unit_cost_snapshot=unit_cost_snapshot,
                suggested_unit_price=suggested_unit_price,
                payment_method=payment_method,
                sold_at=sold_at,
                customer=customer.strip() or None,
                note=note.strip() or None,
            )
            session.add(sale)
            session.flush()
            session.add(
                CashEntry(
                    type="ENTRADA",
                    amount=total,
                    description=f"Venda: {product_name} x{quantity:g}",
                    date=sold_at,
                    sale_id=sale.id,
                )
            )
            session.commit()
            st.toast("Venda registrada com sucesso.", icon="✅")
            st.rerun()

    st.divider()
    st.subheader("Últimas vendas")
    sales = session.query(Sale).order_by(Sale.sold_at.desc()).limit(50).all()
    if not sales:
        st.caption("Nenhuma venda registrada ainda.")
    for sale in sales:
        c1, c2, c3 = st.columns([3, 2, 1])
        status_tag = "  🚫 cancelada" if sale.status == "CANCELADA" else ""
        c1.write(f"**{sale.product_name}**{status_tag}  \n:gray[{format_datetime(sale.sold_at)} · {sale.quantity:g}x · {PAYMENT_LABELS[sale.payment_method]}]")
        value_text = format_currency(sale.quantity * sale.unit_price_charged)
        c2.write(f"~~{value_text}~~" if sale.status == "CANCELADA" else f"**{value_text}**")
        if sale.status == "ATIVA":
            if c3.button("Cancelar", key=f"cancel_{sale.id}"):
                st.session_state[f"confirm_cancel_{sale.id}"] = True
        if st.session_state.get(f"confirm_cancel_{sale.id}"):
            st.warning(
                "Cancelar esta venda? Um lançamento de estorno será criado no fluxo de caixa "
                "e o registro original ficará marcado como cancelado."
            )
            cc1, cc2 = st.columns(2)
            if cc1.button("Sim, cancelar", key=f"confirm_yes_{sale.id}", type="primary"):
                sale.status = "CANCELADA"
                original_entry = (
                    session.query(CashEntry)
                    .filter(CashEntry.sale_id == sale.id, CashEntry.status == "ATIVO")
                    .first()
                )
                if original_entry:
                    original_entry.status = "ESTORNADO"
                    session.add(
                        CashEntry(
                            type="SAIDA",
                            amount=original_entry.amount,
                            description=f"Estorno da venda: {sale.product_name}",
                            date=datetime.now(timezone.utc),
                            sale_id=sale.id,
                            reversal_of_id=original_entry.id,
                        )
                    )
                session.commit()
                del st.session_state[f"confirm_cancel_{sale.id}"]
                st.rerun()
            if cc2.button("Não", key=f"confirm_no_{sale.id}"):
                del st.session_state[f"confirm_cancel_{sale.id}"]
                st.rerun()
finally:
    session.close()
