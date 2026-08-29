"""Remove os dados de simulação/teste: vendas, lançamentos de caixa e receitas.

Mantém intactos: login (User), insumos (Ingredient/IngredientPriceHistory),
categorias de despesa (ExpenseCategory) e configurações (BusinessConfig).

Rode com DATABASE_URL apontando para o banco desejado:
    $env:DATABASE_URL="postgresql://..."
    python clear_simulation_data.py
"""
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, CashEntry, Recipe, RecipeIngredient, Sale


def get_engine():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("Defina DATABASE_URL antes de rodar este script.")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return create_engine(url, connect_args={"sslmode": "require"})


def main():
    engine = get_engine()
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    counts_before = {
        "Vendas": session.query(Sale).count(),
        "Lançamentos de caixa": session.query(CashEntry).count(),
        "Receitas": session.query(Recipe).count(),
    }
    print("Antes de apagar:")
    for label, count in counts_before.items():
        print(f"  {label}: {count}")

    session.query(CashEntry).delete()
    session.query(Sale).delete()
    session.query(RecipeIngredient).delete()
    session.query(Recipe).delete()
    session.commit()

    print("\nDepois de apagar:")
    print(f"  Vendas: {session.query(Sale).count()}")
    print(f"  Lançamentos de caixa: {session.query(CashEntry).count()}")
    print(f"  Receitas: {session.query(Recipe).count()}")

    print("\nMantidos: usuário de login, insumos, categorias de despesa e configurações.")
    session.close()


if __name__ == "__main__":
    main()
