"""Modelos do banco de dados da A.R Confeitaria (SQLAlchemy).

Mesma modelagem do app Next.js original, traduzida para Python. Funciona tanto em
SQLite (desenvolvimento local) quanto em Postgres (produção no Streamlit Cloud) sem
nenhuma mudança de código — a engine é escolhida em db.py.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def gen_id() -> str:
    return uuid.uuid4().hex


def now() -> datetime:
    return datetime.now(timezone.utc)


# Preparado para múltiplos usuários no futuro; hoje só a conta de login existe aqui.
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_id)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String)
    created_at = Column(DateTime(timezone=True), default=now)


# Configurações do negócio (Módulo 0). Linha única, editável a qualquer momento —
# mudanças valem só para novos cálculos, vendas já registradas guardam seu próprio snapshot.
class BusinessConfig(Base):
    __tablename__ = "business_config"

    id = Column(String, primary_key=True, default=gen_id)
    hours_per_day = Column(Float, nullable=False, default=8)
    days_per_week = Column(Float, nullable=False, default=5)
    monthly_salary = Column(Float, nullable=False, default=2000)
    monthly_fixed_costs = Column(Float, nullable=False, default=442)
    tax_rate = Column(Float, nullable=False, default=0)
    commission_rate = Column(Float, nullable=False, default=0)
    cento_discount = Column(Float, nullable=False, default=0.10)
    weeks_per_month = Column(Float, nullable=False, default=4.28)
    fixed_cost_rate_constant = Column(Float, nullable=False, default=1400)
    updated_at = Column(DateTime(timezone=True), default=now, onupdate=now)


# Insumos (Módulo 1): ingredientes e materiais comprados para produção.
class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    purchase_unit = Column(String, nullable=False)
    current_price = Column(Float, nullable=False)
    package_quantity = Column(Float, nullable=False)
    cost_per_unit = Column(Float, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=now)
    updated_at = Column(DateTime(timezone=True), default=now, onupdate=now)

    price_history = relationship(
        "IngredientPriceHistory",
        back_populates="ingredient",
        cascade="all, delete-orphan",
        order_by="desc(IngredientPriceHistory.effective_from)",
    )


# Histórico de preços do insumo: nunca sobrescrito, cada mudança de preço gera uma linha nova.
class IngredientPriceHistory(Base):
    __tablename__ = "ingredient_price_history"

    id = Column(String, primary_key=True, default=gen_id)
    ingredient_id = Column(String, ForeignKey("ingredients.id"), nullable=False)
    price = Column(Float, nullable=False)
    package_quantity = Column(Float, nullable=False)
    cost_per_unit = Column(Float, nullable=False)
    effective_from = Column(DateTime(timezone=True), default=now)

    ingredient = relationship("Ingredient", back_populates="price_history")


# Receitas/Produtos (Módulo 2).
class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    yield_quantity = Column(Float, nullable=False)
    prep_time_minutes = Column(Float, nullable=False)
    cards_tags_cost = Column(Float, nullable=False, default=0)
    packaging_cost = Column(Float, nullable=False, default=0)
    other_costs = Column(Float, nullable=False, default=0)
    profit_multiplier = Column(Float, nullable=False, default=1)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=now)
    updated_at = Column(DateTime(timezone=True), default=now, onupdate=now)

    ingredients = relationship(
        "RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan"
    )


# Ingredientes usados em cada receita, com a quantidade usada (na mesma unidade de compra do insumo).
class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id = Column(String, primary_key=True, default=gen_id)
    recipe_id = Column(String, ForeignKey("recipes.id"), nullable=False)
    ingredient_id = Column(String, ForeignKey("ingredients.id"), nullable=False)
    quantity_used = Column(Float, nullable=False)

    recipe = relationship("Recipe", back_populates="ingredients")
    ingredient = relationship("Ingredient")


PAYMENT_METHODS = ["DINHEIRO", "PIX", "DEBITO", "CREDITO"]
PAYMENT_LABELS = {
    "DINHEIRO": "Dinheiro",
    "PIX": "Pix",
    "DEBITO": "Cartão débito",
    "CREDITO": "Cartão crédito",
}


# Vendas (Módulo 3). Guarda snapshot de custo e preço sugerido no momento da venda,
# para que o lucro por produto (Módulo 5) não mude se a receita/config for editada depois.
class Sale(Base):
    __tablename__ = "sales"

    id = Column(String, primary_key=True, default=gen_id)
    recipe_id = Column(String, ForeignKey("recipes.id"), nullable=True)
    product_name = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price_charged = Column(Float, nullable=False)
    unit_cost_snapshot = Column(Float, nullable=False)
    suggested_unit_price = Column(Float, nullable=True)
    payment_method = Column(String, nullable=False)
    sold_at = Column(DateTime(timezone=True), default=now)
    customer = Column(String, nullable=True)
    note = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="ATIVA")  # ATIVA | CANCELADA
    created_at = Column(DateTime(timezone=True), default=now)

    recipe = relationship("Recipe")


class ExpenseCategory(Base):
    __tablename__ = "expense_categories"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now)


# Fluxo de caixa (Módulo 4). Vendas geram uma entrada automaticamente (via sale_id).
# Nada é apagado: estornos criam um novo lançamento e marcam o original como ESTORNADO.
class CashEntry(Base):
    __tablename__ = "cash_entries"

    id = Column(String, primary_key=True, default=gen_id)
    type = Column(String, nullable=False)  # ENTRADA | SAIDA
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=False)
    date = Column(DateTime(timezone=True), default=now)
    category_id = Column(String, ForeignKey("expense_categories.id"), nullable=True)
    sale_id = Column(String, ForeignKey("sales.id"), nullable=True)
    status = Column(String, nullable=False, default="ATIVO")  # ATIVO | ESTORNADO
    reversal_of_id = Column(String, ForeignKey("cash_entries.id"), nullable=True, unique=True)
    created_at = Column(DateTime(timezone=True), default=now)

    category = relationship("ExpenseCategory")
