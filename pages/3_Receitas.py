"""Módulo 2 — Receitas/Produtos e cálculo de preço de venda.

Replica a lógica da planilha "precificação_Nova.xlsx" (ver pricing.py). A prévia do
cálculo é recalculada a cada interação, antes mesmo de salvar a receita.
"""
import streamlit as st

from db import ensure_business_config, get_session
from format_utils import format_currency
from models import Ingredient, Recipe, RecipeIngredient
from pricing import (
    PricingIngredientInput,
    PricingRecipeInput,
    calculate_recipe_pricing,
    config_to_pricing_input,
)

st.title("📖 Receitas / Produtos")
st.caption("Cadastro e cálculo automático de preço de venda.")

session = get_session()
try:
    config = ensure_business_config(session)
    pricing_config = config_to_pricing_input(config)
    all_ingredients = session.query(Ingredient).filter(Ingredient.active == True).order_by(Ingredient.name).all()  # noqa: E712

    def render_breakdown(breakdown):
        st.markdown("##### Prévia do cálculo")
        rows = [
            ("Custo de materiais (ingredientes)", breakdown.custo_materiais),
            ("Outros custos diretos", breakdown.outros_custos),
            ("Custo de mão de obra", breakdown.custo_horas),
            ("Total parcial", breakdown.total_parcial),
            ("Margem de lucro", breakdown.margem_lucro),
            ("Impostos", breakdown.impostos),
            ("Comissões", breakdown.comissoes),
            ("Custos fixos (rateio)", breakdown.custos_fixos),
        ]
        for label, value in rows:
            c1, c2 = st.columns([3, 2])
            c1.write(label)
            c2.write(format_currency(value))
        c1, c2 = st.columns(2)
        c1.metric("Preço sugerido (unidade)", format_currency(breakdown.preco_unidade))
        c2.metric("Preço sugerido (cento)", format_currency(breakdown.preco_cento))

    def render_ingredient_rows(state_key: str, ingredients: list[Ingredient]):
        rows = st.session_state[state_key]
        options = {i.id: i for i in ingredients}
        to_remove = None
        for row in rows:
            c1, c2, c3 = st.columns([3, 2, 1])
            names = [i.name for i in ingredients]
            ids = [i.id for i in ingredients]
            current_idx = ids.index(row["ingredient_id"]) if row["ingredient_id"] in ids else 0
            chosen = c1.selectbox(
                "Ingrediente", names, index=current_idx if names else 0, key=f"{state_key}_ing_{row['key']}", label_visibility="collapsed"
            )
            row["ingredient_id"] = ids[names.index(chosen)] if names else None
            unit = options[row["ingredient_id"]].purchase_unit if row["ingredient_id"] else ""
            row["quantity"] = c2.number_input(
                f"Qtd. ({unit})", min_value=0.0, value=row["quantity"], step=0.01,
                key=f"{state_key}_qty_{row['key']}", label_visibility="collapsed",
            )
            if c3.button("✕", key=f"{state_key}_rm_{row['key']}"):
                to_remove = row["key"]
        if to_remove is not None:
            st.session_state[state_key] = [r for r in rows if r["key"] != to_remove]
            st.rerun()
        if st.button("+ Adicionar ingrediente", key=f"{state_key}_add"):
            next_key = max([r["key"] for r in rows], default=-1) + 1
            st.session_state[state_key].append({"key": next_key, "ingredient_id": ingredients[0].id if ingredients else None, "quantity": 0.0})
            st.rerun()
        return st.session_state[state_key]

    def build_pricing_input(rows, yield_quantity, prep_time_minutes, cards_tags_cost, packaging_cost, other_costs, profit_multiplier):
        ing_by_id = {i.id: i for i in all_ingredients}
        ingredients_input = [
            PricingIngredientInput(quantity_used=r["quantity"], cost_per_unit=ing_by_id[r["ingredient_id"]].cost_per_unit)
            for r in rows
            if r["ingredient_id"] and r["quantity"] > 0 and r["ingredient_id"] in ing_by_id
        ]
        return PricingRecipeInput(
            yield_quantity=yield_quantity,
            prep_time_minutes=prep_time_minutes,
            cards_tags_cost=cards_tags_cost,
            packaging_cost=packaging_cost,
            other_costs=other_costs,
            profit_multiplier=profit_multiplier,
            ingredients=ingredients_input,
        )

    tab_list, tab_new = st.tabs(["Lista", "➕ Nova receita"])

    with tab_new:
        if not all_ingredients:
            st.warning("Cadastre insumos primeiro (na aba Insumos) para poder montar uma receita.")
        else:
            state_key = "new_recipe_rows"
            if state_key not in st.session_state:
                st.session_state[state_key] = [{"key": 0, "ingredient_id": all_ingredients[0].id, "quantity": 0.0}]

            col_form, col_preview = st.columns([3, 2])
            with col_form:
                name = st.text_input("Nome do produto", placeholder="Ex: Bolo de Chocolate 20cm")
                c1, c2 = st.columns(2)
                yield_quantity = c1.number_input("Rendimento", min_value=0.01, value=1.0, help="Quantas unidades esta receita gera")
                prep_time_minutes = c2.number_input("Tempo de preparo (min)", min_value=0.0, value=0.0)

                st.markdown("**Ingredientes usados**")
                rows = render_ingredient_rows(state_key, all_ingredients)

                st.markdown("**Outros custos diretos (R$)**")
                c3, c4, c5 = st.columns(3)
                cards_tags_cost = c3.number_input("Cartões/tags", min_value=0.0, value=0.0, key="new_cards")
                packaging_cost = c4.number_input("Embalagem", min_value=0.0, value=0.0, key="new_pack")
                other_costs = c5.number_input("Outros", min_value=0.0, value=0.0, key="new_other")

                profit_multiplier = st.number_input(
                    "Margem de lucro desejada",
                    min_value=0.0,
                    value=1.0,
                    step=0.1,
                    help="Multiplicador sobre o custo, não é porcentagem. Ex.: 1 = soma 100% do custo (dobra o preço) · 0,5 = soma 50% do custo.",
                    key="new_profit",
                )

            recipe_input = build_pricing_input(rows, yield_quantity, prep_time_minutes, cards_tags_cost, packaging_cost, other_costs, profit_multiplier)
            breakdown = calculate_recipe_pricing(recipe_input, pricing_config)
            with col_preview:
                render_breakdown(breakdown)

            if st.button("Cadastrar receita", type="primary", use_container_width=True):
                valid_rows = [r for r in rows if r["ingredient_id"] and r["quantity"] > 0]
                if not name.strip():
                    st.error("Informe o nome da receita.")
                elif yield_quantity <= 0:
                    st.error("O rendimento deve ser maior que zero.")
                elif not valid_rows:
                    st.error("Adicione ao menos um ingrediente com quantidade maior que zero.")
                else:
                    recipe = Recipe(
                        name=name.strip(),
                        yield_quantity=yield_quantity,
                        prep_time_minutes=prep_time_minutes,
                        cards_tags_cost=cards_tags_cost,
                        packaging_cost=packaging_cost,
                        other_costs=other_costs,
                        profit_multiplier=profit_multiplier,
                    )
                    session.add(recipe)
                    session.flush()
                    for r in valid_rows:
                        session.add(
                            RecipeIngredient(recipe_id=recipe.id, ingredient_id=r["ingredient_id"], quantity_used=r["quantity"])
                        )
                    session.commit()
                    del st.session_state[state_key]
                    st.toast(f"Receita '{name}' cadastrada.", icon="✅")
                    st.rerun()

    with tab_list:
        recipes = session.query(Recipe).order_by(Recipe.active.desc(), Recipe.name.asc()).all()
        if not recipes:
            st.info("Nenhuma receita cadastrada ainda.")
        for recipe in recipes:
            recipe_input = PricingRecipeInput(
                yield_quantity=recipe.yield_quantity,
                prep_time_minutes=recipe.prep_time_minutes,
                cards_tags_cost=recipe.cards_tags_cost,
                packaging_cost=recipe.packaging_cost,
                other_costs=recipe.other_costs,
                profit_multiplier=recipe.profit_multiplier,
                ingredients=[
                    PricingIngredientInput(quantity_used=ri.quantity_used, cost_per_unit=ri.ingredient.cost_per_unit)
                    for ri in recipe.ingredients
                ],
            )
            breakdown = calculate_recipe_pricing(recipe_input, pricing_config)
            label = f"{recipe.name} — {format_currency(breakdown.preco_unidade)}/un." + ("" if recipe.active else "  ·  inativa")

            with st.expander(label):
                state_key = f"edit_recipe_rows_{recipe.id}"
                if state_key not in st.session_state:
                    st.session_state[state_key] = [
                        {"key": idx, "ingredient_id": ri.ingredient_id, "quantity": ri.quantity_used}
                        for idx, ri in enumerate(recipe.ingredients)
                    ] or [{"key": 0, "ingredient_id": all_ingredients[0].id if all_ingredients else None, "quantity": 0.0}]

                edit_ingredients = all_ingredients.copy()
                used_inactive = [ri.ingredient for ri in recipe.ingredients if not ri.ingredient.active]
                for ing in used_inactive:
                    if ing.id not in [i.id for i in edit_ingredients]:
                        edit_ingredients.append(ing)

                col_form, col_preview = st.columns([3, 2])
                with col_form:
                    name = st.text_input("Nome do produto", value=recipe.name, key=f"name_{recipe.id}")
                    c1, c2 = st.columns(2)
                    yield_quantity = c1.number_input("Rendimento", min_value=0.01, value=float(recipe.yield_quantity), key=f"yield_{recipe.id}")
                    prep_time_minutes = c2.number_input("Tempo de preparo (min)", min_value=0.0, value=float(recipe.prep_time_minutes), key=f"prep_{recipe.id}")

                    st.markdown("**Ingredientes usados**")
                    rows = render_ingredient_rows(state_key, edit_ingredients)

                    st.markdown("**Outros custos diretos (R$)**")
                    c3, c4, c5 = st.columns(3)
                    cards_tags_cost = c3.number_input("Cartões/tags", min_value=0.0, value=float(recipe.cards_tags_cost), key=f"cards_{recipe.id}")
                    packaging_cost = c4.number_input("Embalagem", min_value=0.0, value=float(recipe.packaging_cost), key=f"pack_{recipe.id}")
                    other_costs = c5.number_input("Outros", min_value=0.0, value=float(recipe.other_costs), key=f"other_{recipe.id}")

                    profit_multiplier = st.number_input(
                        "Margem de lucro desejada",
                        min_value=0.0,
                        value=float(recipe.profit_multiplier),
                        step=0.1,
                        key=f"profit_{recipe.id}",
                        help="Multiplicador sobre o custo. Ex.: 1 = soma 100% do custo (dobra o preço) · 0,5 = soma 50%.",
                    )

                edit_input = build_pricing_input(rows, yield_quantity, prep_time_minutes, cards_tags_cost, packaging_cost, other_costs, profit_multiplier)
                edit_breakdown = calculate_recipe_pricing(edit_input, pricing_config)
                with col_preview:
                    render_breakdown(edit_breakdown)

                b1, b2 = st.columns(2)
                if b1.button("Salvar alterações", key=f"save_{recipe.id}", type="primary"):
                    valid_rows = [r for r in rows if r["ingredient_id"] and r["quantity"] > 0]
                    if not valid_rows:
                        st.error("Adicione ao menos um ingrediente com quantidade maior que zero.")
                    else:
                        recipe.name = name.strip() or recipe.name
                        recipe.yield_quantity = yield_quantity
                        recipe.prep_time_minutes = prep_time_minutes
                        recipe.cards_tags_cost = cards_tags_cost
                        recipe.packaging_cost = packaging_cost
                        recipe.other_costs = other_costs
                        recipe.profit_multiplier = profit_multiplier
                        session.query(RecipeIngredient).filter(RecipeIngredient.recipe_id == recipe.id).delete()
                        for r in valid_rows:
                            session.add(RecipeIngredient(recipe_id=recipe.id, ingredient_id=r["ingredient_id"], quantity_used=r["quantity"]))
                        session.commit()
                        st.toast("Receita atualizada.", icon="✅")
                        st.rerun()

                toggle_label = "Marcar como inativa" if recipe.active else "Reativar"
                if b2.button(toggle_label, key=f"toggle_{recipe.id}"):
                    recipe.active = not recipe.active
                    session.commit()
                    st.rerun()
finally:
    session.close()
