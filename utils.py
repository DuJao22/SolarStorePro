
def format_price(value):
    """Formata preço no padrão brasileiro R$ 1.234,56"""
    try:
        value = float(value)
        return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return "R$ 0,00"
