"""Formatação de valores no padrão brasileiro (R$, datas dd/mm/aaaa)."""
from datetime import datetime


def format_currency(value: float | None) -> str:
    value = value or 0
    text = f"{value:,.2f}"
    text = text.replace(",", "§").replace(".", ",").replace("§", ".")
    return f"R$ {text}"


def format_number(value: float | None, decimals: int = 2) -> str:
    value = value or 0
    text = f"{value:,.{decimals}f}"
    text = text.replace(",", "§").replace(".", ",").replace("§", ".")
    return text


def format_percent(fraction: float | None) -> str:
    fraction = fraction or 0
    return format_number(fraction * 100, 2) + "%"


def format_date(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.strftime("%d/%m/%Y")


def format_datetime(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.strftime("%d/%m/%Y %H:%M")
