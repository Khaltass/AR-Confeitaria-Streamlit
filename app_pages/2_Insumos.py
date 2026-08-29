"""Módulo 1 — Insumos (ingredientes e materiais)."""
import streamlit as st

from auth import require_login
from db import get_session
from format_utils import format_currency, format_datetime, format_number
from models import Ingredient, IngredientPriceHistory

require_login()

UNITS = ["kg", "g", "L", "ml", "unidade"]

st.title("📦 Insumos")
st.caption("Ingredientes e materiais usados na produção.")

session = get_session()
try:
    tab_list, tab_new = st.tabs(["Lista", "➕ Novo insumo"])

    with tab_new:
        with st.form("new_ingredient", clear_on_submit=True):
            name = st.text_input("Nome do insumo", placeholder="Ex: Farinha de trigo")
            category = st.text_input("Categoria", placeholder="Ex: Ingrediente, Embalagem")
            purchase_unit = st.selectbox("Unidade de compra", UNITS)
            c1, c2 = st.columns(2)
            current_price = c1.number_input("Preço pago (R$)", min_value=0.0, step=0.5)
            package_quantity = c2.number_input("Quantidade da embalagem", min_value=0.001, value=1.0, step=0.1)
            st.caption("O custo por unidade de medida é calculado automaticamente (preço ÷ quantidade da embalagem).")
            submitted = st.form_submit_button("Cadastrar insumo", type="primary", use_container_width=True)

        if submitted:
            if not name.strip():
                st.error("Informe o nome do insumo.")
            elif package_quantity <= 0:
                st.error("A quantidade da embalagem deve ser maior que zero.")
            else:
                cost_per_unit = current_price / package_quantity
                ingredient = Ingredient(
                    name=name.strip(),
                    category=category.strip() or "Outros",
                    purchase_unit=purchase_unit,
                    current_price=current_price,
                    package_quantity=package_quantity,
                    cost_per_unit=cost_per_unit,
                )
                session.add(ingredient)
                session.flush()
                session.add(
                    IngredientPriceHistory(
                        ingredient_id=ingredient.id,
                        price=current_price,
                        package_quantity=package_quantity,
                        cost_per_unit=cost_per_unit,
                    )
                )
                session.commit()
                st.toast(f"Insumo '{name}' cadastrado.", icon="✅")
                st.rerun()

    with tab_list:
        ingredients = (
            session.query(Ingredient).order_by(Ingredient.active.desc(), Ingredient.name.asc()).all()
        )
        if not ingredients:
            st.info("Nenhum insumo cadastrado ainda.")
        for ing in ingredients:
            label = ing.name + ("" if ing.active else "  ·  inativo")
            with st.expander(label):
                st.caption(
                    f"{ing.category} · {format_number(ing.package_quantity)} {ing.purchase_unit} "
                    f"por {format_currency(ing.current_price)}  →  {format_currency(ing.cost_per_unit)}/{ing.purchase_unit}"
                )

                with st.form(f"edit_{ing.id}"):
                    name = st.text_input("Nome", value=ing.name, key=f"name_{ing.id}")
                    category = st.text_input("Categoria", value=ing.category, key=f"cat_{ing.id}")
                    purchase_unit = st.selectbox(
                        "Unidade", UNITS, index=UNITS.index(ing.purchase_unit), key=f"unit_{ing.id}"
                    )
                    c1, c2 = st.columns(2)
                    current_price = c1.number_input(
                        "Preço pago (R$)", min_value=0.0, value=float(ing.current_price), key=f"price_{ing.id}"
                    )
                    package_quantity = c2.number_input(
                        "Quantidade da embalagem",
                        min_value=0.001,
                        value=float(ing.package_quantity),
                        key=f"qty_{ing.id}",
                    )
                    save = st.form_submit_button("Salvar alterações")

                if save:
                    if package_quantity <= 0:
                        st.error("A quantidade da embalagem deve ser maior que zero.")
                    else:
                        cost_per_unit = current_price / package_quantity
                        price_changed = (
                            ing.current_price != current_price or ing.package_quantity != package_quantity
                        )
                        ing.name = name.strip() or ing.name
                        ing.category = category.strip() or "Outros"
                        ing.purchase_unit = purchase_unit
                        ing.current_price = current_price
                        ing.package_quantity = package_quantity
                        ing.cost_per_unit = cost_per_unit
                        if price_changed:
                            session.add(
                                IngredientPriceHistory(
                                    ingredient_id=ing.id,
                                    price=current_price,
                                    package_quantity=package_quantity,
                                    cost_per_unit=cost_per_unit,
                                )
                            )
                        session.commit()
                        st.toast("Insumo atualizado.", icon="✅")
                        st.rerun()

                toggle_label = "Marcar como inativo" if ing.active else "Reativar"
                if st.button(toggle_label, key=f"toggle_{ing.id}"):
                    ing.active = not ing.active
                    session.commit()
                    st.rerun()

                history = (
                    session.query(IngredientPriceHistory)
                    .filter(IngredientPriceHistory.ingredient_id == ing.id)
                    .order_by(IngredientPriceHistory.effective_from.desc())
                    .all()
                )
                if history:
                    st.caption("Histórico de preços")
                    for h in history:
                        st.write(
                            f"- {format_currency(h.price)} por {format_number(h.package_quantity)} "
                            f"{ing.purchase_unit}  ({format_datetime(h.effective_from)})"
                        )
finally:
    session.close()
