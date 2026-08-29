"""Popula o banco com dados de exemplo: login, insumos, receitas, vendas e caixa.

Rode com `python seed.py` (dentro do venv). Igual ao seed do app Next.js original —
mesmos dados, para dar pra comparar. Roda tudo dentro do próprio processo Python
(sem depender do Streamlit rodando), então funciona tanto contra SQLite local
quanto contra o Postgres de produção (defina DATABASE_URL no ambiente antes de rodar).

⚠️ Apaga receitas, insumos, vendas e lançamentos de caixa existentes antes de recriar
os dados de exemplo. Rode só no início — nunca depois de já ter dados reais.
"""
import os
import sys

if sys.platform == "win32":
    # Evita caracteres acentuados quebrados no console do Windows (cp1252 por padrão).
    sys.stdout.reconfigure(encoding="utf-8")

import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import (
    Base,
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
from pricing import calculate_recipe_pricing, config_to_pricing_input, recipe_to_pricing_input


def get_engine():
    url = os.environ.get("DATABASE_URL")
    if url:
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return create_engine(url, connect_args={"sslmode": "require"})
    from pathlib import Path

    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{data_dir / 'app.db'}")


def main():
    engine = get_engine()
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("Populando banco de dados de exemplo da A.R Confeitaria...\n")

    # ---------- Usuário (login) ----------
    login_username = os.environ.get("LOGIN_USERNAME", "amanda").strip().lower()
    login_password = os.environ.get("LOGIN_PASSWORD", "lucky123")
    password_hash = bcrypt.hashpw(login_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    session.query(User).delete()
    session.add(User(username=login_username, password_hash=password_hash, name="Administradora"))
    print(f"Usuário de login: {login_username} / senha: {login_password}")

    # ---------- Módulo 0: Configurações ----------
    session.query(BusinessConfig).delete()
    config = BusinessConfig(
        hours_per_day=8,
        days_per_week=5,
        monthly_salary=2000,
        monthly_fixed_costs=442,
        tax_rate=0,
        commission_rate=0,
        cento_discount=0.10,
        weeks_per_month=4.28,
        fixed_cost_rate_constant=1400,
    )
    session.add(config)
    print("Configurações do negócio criadas (valores padrão da planilha).")

    # ---------- Módulo 1: Insumos ----------
    session.query(IngredientPriceHistory).delete()
    session.query(RecipeIngredient).delete()
    session.query(Ingredient).delete()

    ingredient_defs = [
        ("Farinha de trigo", "Ingrediente", "kg", 5.0, 1),
        ("Açúcar refinado", "Ingrediente", "kg", 4.5, 1),
        ("Chocolate em pó 50%", "Ingrediente", "kg", 22.0, 1),
        ("Manteiga sem sal", "Ingrediente", "kg", 16.0, 0.5),
        ("Ovos", "Ingrediente", "unidade", 12.0, 12),
        ("Leite integral", "Ingrediente", "L", 4.8, 1),
        ("Fermento em pó", "Ingrediente", "g", 8.0, 100),
        ("Leite condensado", "Ingrediente", "g", 6.5, 395),
        ("Chocolate granulado", "Ingrediente", "g", 18.0, 1000),
        ("Forminhas de papel nº 5", "Embalagem", "unidade", 8.0, 100),
    ]
    ingredients = {}
    for name, category, unit, price, qty in ingredient_defs:
        cost_per_unit = price / qty
        ing = Ingredient(
            name=name, category=category, purchase_unit=unit,
            current_price=price, package_quantity=qty, cost_per_unit=cost_per_unit,
        )
        session.add(ing)
        session.flush()
        session.add(IngredientPriceHistory(ingredient_id=ing.id, price=price, package_quantity=qty, cost_per_unit=cost_per_unit))
        ingredients[name] = ing
    print(f"{len(ingredient_defs)} insumos cadastrados.")

    # ---------- Categorias de despesa ----------
    session.query(ExpenseCategory).delete()
    category_names = ["Insumos", "Embalagens", "Gás", "Energia", "Aluguel", "Retirada", "Outros"]
    categories = {}
    for name in category_names:
        cat = ExpenseCategory(name=name)
        session.add(cat)
        session.flush()
        categories[name] = cat
    print(f"{len(category_names)} categorias de despesa criadas.")

    # ---------- Módulo 2: Receitas de exemplo ----------
    session.query(Sale).delete()
    session.query(CashEntry).delete()
    session.query(Recipe).delete()

    bolo = Recipe(
        name="Bolo de Chocolate 20cm", yield_quantity=1, prep_time_minutes=90,
        cards_tags_cost=2.0, packaging_cost=5.0, other_costs=0, profit_multiplier=1,
    )
    session.add(bolo)
    session.flush()
    for ing_name, qty in [
        ("Farinha de trigo", 0.5), ("Açúcar refinado", 0.4), ("Chocolate em pó 50%", 0.15),
        ("Manteiga sem sal", 0.2), ("Ovos", 4), ("Leite integral", 0.25), ("Fermento em pó", 15),
    ]:
        session.add(RecipeIngredient(recipe_id=bolo.id, ingredient_id=ingredients[ing_name].id, quantity_used=qty))

    brigadeiro = Recipe(
        name="Brigadeiro Gourmet (rende 10 un.)", yield_quantity=10, prep_time_minutes=40,
        cards_tags_cost=0, packaging_cost=3.0, other_costs=0, profit_multiplier=0.8,
    )
    session.add(brigadeiro)
    session.flush()
    for ing_name, qty in [
        ("Leite condensado", 395), ("Chocolate em pó 50%", 0.03), ("Manteiga sem sal", 0.02),
        ("Chocolate granulado", 50), ("Forminhas de papel nº 5", 10),
    ]:
        session.add(RecipeIngredient(recipe_id=brigadeiro.id, ingredient_id=ingredients[ing_name].id, quantity_used=qty))

    session.flush()
    session.refresh(bolo)
    session.refresh(brigadeiro)
    print("\n2 receitas de exemplo criadas: 'Bolo de Chocolate 20cm' (rendimento 1) e 'Brigadeiro Gourmet' (rendimento 10).")

    pricing_config = config_to_pricing_input(config)

    def print_breakdown(label, recipe):
        breakdown = calculate_recipe_pricing(recipe_to_pricing_input(recipe), pricing_config)
        print(f"\n[{label}]")
        print(f"  Custo materiais:  R$ {breakdown.custo_materiais:.2f}")
        print(f"  Outros custos:    R$ {breakdown.outros_custos:.2f}")
        print(f"  Custo horas:      R$ {breakdown.custo_horas:.2f}")
        print(f"  Total parcial:    R$ {breakdown.total_parcial:.2f}")
        print(f"  Margem de lucro:  R$ {breakdown.margem_lucro:.2f}")
        print(f"  Impostos:         R$ {breakdown.impostos:.2f}")
        print(f"  Comissões:        R$ {breakdown.comissoes:.2f}")
        print(f"  Custos fixos:     R$ {breakdown.custos_fixos:.2f}")
        print(f"  >> Preço unidade: R$ {breakdown.preco_unidade:.2f}")
        print(f"  >> Preço cento:   R$ {breakdown.preco_cento:.2f}")
        return breakdown

    breakdown_bolo = print_breakdown("Bolo de Chocolate 20cm (rendimento 1)", bolo)
    breakdown_brigadeiro = print_breakdown("Brigadeiro Gourmet (rendimento 10)", brigadeiro)

    # ---------- Módulo 3 e 4: Vendas de exemplo + fluxo de caixa ----------
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)

    def registrar_venda(recipe, product_name, quantity, unit_price, unit_cost, suggested_price, payment_method, days_ago, customer=None):
        sold_at = now - timedelta(days=days_ago)
        sale = Sale(
            recipe_id=recipe.id if recipe else None,
            product_name=product_name, quantity=quantity, unit_price_charged=unit_price,
            unit_cost_snapshot=unit_cost, suggested_unit_price=suggested_price,
            payment_method=payment_method, sold_at=sold_at, customer=customer,
        )
        session.add(sale)
        session.flush()
        session.add(CashEntry(type="ENTRADA", amount=quantity * unit_price, description=f"Venda: {product_name} x{quantity:g}", date=sold_at, sale_id=sale.id))

    registrar_venda(bolo, bolo.name, 1, breakdown_bolo.preco_unidade, breakdown_bolo.custo_producao_unidade, breakdown_bolo.preco_unidade, "PIX", 1, "Maria Silva")
    registrar_venda(bolo, bolo.name, 1, breakdown_bolo.preco_unidade - 5, breakdown_bolo.custo_producao_unidade, breakdown_bolo.preco_unidade, "CREDITO", 6)
    registrar_venda(brigadeiro, brigadeiro.name, 3, breakdown_brigadeiro.preco_unidade, breakdown_brigadeiro.custo_producao_unidade, breakdown_brigadeiro.preco_unidade, "DINHEIRO", 0, "Ana Souza")
    registrar_venda(brigadeiro, brigadeiro.name, 5, breakdown_brigadeiro.preco_unidade, breakdown_brigadeiro.custo_producao_unidade, breakdown_brigadeiro.preco_unidade, "PIX", 3)
    registrar_venda(brigadeiro, brigadeiro.name, 2, breakdown_brigadeiro.preco_unidade, breakdown_brigadeiro.custo_producao_unidade, breakdown_brigadeiro.preco_unidade, "DEBITO", 12)

    avulso = Sale(
        recipe_id=None, product_name="Encomenda especial - Torta de morango", quantity=1,
        unit_price_charged=120, unit_cost_snapshot=0, suggested_unit_price=None,
        payment_method="PIX", sold_at=now - timedelta(days=2), customer="Carla Mendes",
        note="Encomenda de aniversário",
    )
    session.add(avulso)
    session.flush()
    session.add(CashEntry(type="ENTRADA", amount=120, description=f"Venda: {avulso.product_name} x1", date=avulso.sold_at, sale_id=avulso.id))

    manual_entries = [
        ("SAIDA", 60, "Compra de gás de cozinha", "Gás", 8),
        ("SAIDA", 150, "Conta de energia", "Energia", 10),
        ("SAIDA", 800, "Aluguel do mês", "Aluguel", 15),
        ("SAIDA", 200, "Compra de insumos no atacado", "Insumos", 4),
        ("ENTRADA", 50, "Venda de embalagens excedentes", None, 5),
    ]
    for entry_type, amount, description, category_name, days_ago in manual_entries:
        session.add(
            CashEntry(
                type=entry_type, amount=amount, description=description,
                date=now - timedelta(days=days_ago),
                category_id=categories[category_name].id if category_name else None,
            )
        )

    session.commit()
    print("\nVendas e lançamentos de caixa de exemplo criados.")
    print("\nSeed concluído com sucesso.")
    session.close()


if __name__ == "__main__":
    main()
