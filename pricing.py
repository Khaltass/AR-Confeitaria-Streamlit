"""Motor de cálculo de preço de venda (Módulo 2).

Port exato da lógica validada no app Next.js original (src/lib/pricing.ts), que por sua
vez replica a planilha "precificação_Nova.xlsx" da A.R Confeitaria. Não alterar a ordem
ou a fórmula dos passos sem validar com a planilha. As taxas (tax_rate, commission_rate,
cento_discount) são frações (0.10 = 10%), não percentuais.
"""
from dataclasses import dataclass, field


@dataclass
class PricingIngredientInput:
    quantity_used: float
    cost_per_unit: float


@dataclass
class PricingRecipeInput:
    yield_quantity: float
    prep_time_minutes: float
    cards_tags_cost: float
    packaging_cost: float
    other_costs: float
    profit_multiplier: float
    ingredients: list[PricingIngredientInput] = field(default_factory=list)


@dataclass
class PricingConfigInput:
    hours_per_day: float
    days_per_week: float
    monthly_salary: float
    monthly_fixed_costs: float
    tax_rate: float
    commission_rate: float
    cento_discount: float
    weeks_per_month: float
    fixed_cost_rate_constant: float


@dataclass
class PricingBreakdown:
    custo_materiais: float
    outros_custos: float
    valor_hora: float
    custo_horas: float
    total_parcial: float
    margem_lucro: float
    impostos: float
    comissoes: float
    custos_fixos: float
    preco_unidade: float
    preco_cento: float
    # Custo de produção por unidade (sem impostos/comissão/margem), usado para lucro real na venda.
    custo_producao_unidade: float


def calculate_recipe_pricing(
    recipe: PricingRecipeInput, config: PricingConfigInput
) -> PricingBreakdown:
    # 1) Custo dos ingredientes usados nesta receita
    custo_materiais = sum(i.cost_per_unit * i.quantity_used for i in recipe.ingredients)

    # 2) Outros custos diretos (cartões/tags + embalagem + outros)
    outros_custos = recipe.cards_tags_cost + recipe.packaging_cost + recipe.other_costs

    # 3) Custo de mão de obra
    valor_hora = config.monthly_salary / (
        config.hours_per_day * config.days_per_week * config.weeks_per_month
    )
    custo_horas = (recipe.prep_time_minutes / 60) * valor_hora

    # 4) Total parcial
    total_parcial = custo_materiais + outros_custos + custo_horas

    # 5) Margem de lucro (multiplicador sobre o total parcial)
    margem_lucro = recipe.profit_multiplier * total_parcial

    # 6) Impostos (% sobre custo + lucro)
    impostos = (total_parcial + margem_lucro) * config.tax_rate

    # 7) Comissões (% sobre custo + lucro + impostos)
    comissoes = (impostos + total_parcial + margem_lucro) * config.commission_rate

    # 8) Rateio de custos fixos (proporcional ao tempo de preparo desta receita).
    # A constante 1400 é herdada da planilha original, origem não identificada — manter exatamente.
    custos_fixos = (
        (config.monthly_fixed_costs / (config.days_per_week * config.weeks_per_month))
        / config.fixed_cost_rate_constant
    ) * recipe.prep_time_minutes

    yield_quantity = recipe.yield_quantity if recipe.yield_quantity > 0 else 1

    # 9) Preço final por unidade
    preco_unidade = (
        total_parcial + impostos + comissoes + margem_lucro + custos_fixos
    ) / yield_quantity

    # 10) Preço "do cento" (100 unidades, com desconto configurável)
    preco_cento = preco_unidade * 100 * (1 - config.cento_discount)

    custo_producao_unidade = (total_parcial + custos_fixos) / yield_quantity

    return PricingBreakdown(
        custo_materiais=custo_materiais,
        outros_custos=outros_custos,
        valor_hora=valor_hora,
        custo_horas=custo_horas,
        total_parcial=total_parcial,
        margem_lucro=margem_lucro,
        impostos=impostos,
        comissoes=comissoes,
        custos_fixos=custos_fixos,
        preco_unidade=preco_unidade,
        preco_cento=preco_cento,
        custo_producao_unidade=custo_producao_unidade,
    )


def config_to_pricing_input(config) -> PricingConfigInput:
    """Converte um BusinessConfig (linha do banco) no dataclass de entrada do cálculo."""
    return PricingConfigInput(
        hours_per_day=config.hours_per_day,
        days_per_week=config.days_per_week,
        monthly_salary=config.monthly_salary,
        monthly_fixed_costs=config.monthly_fixed_costs,
        tax_rate=config.tax_rate,
        commission_rate=config.commission_rate,
        cento_discount=config.cento_discount,
        weeks_per_month=config.weeks_per_month,
        fixed_cost_rate_constant=config.fixed_cost_rate_constant,
    )


def recipe_to_pricing_input(recipe) -> PricingRecipeInput:
    """Converte um Recipe (com .ingredients carregado) no dataclass de entrada do cálculo."""
    return PricingRecipeInput(
        yield_quantity=recipe.yield_quantity,
        prep_time_minutes=recipe.prep_time_minutes,
        cards_tags_cost=recipe.cards_tags_cost,
        packaging_cost=recipe.packaging_cost,
        other_costs=recipe.other_costs,
        profit_multiplier=recipe.profit_multiplier,
        ingredients=[
            PricingIngredientInput(
                quantity_used=ri.quantity_used, cost_per_unit=ri.ingredient.cost_per_unit
            )
            for ri in recipe.ingredients
        ],
    )
