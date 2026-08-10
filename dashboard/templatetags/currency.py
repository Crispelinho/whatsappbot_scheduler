from django import template

register = template.Library()

@register.filter
def format_currency(value, symbol="$"):
    try:
        if value is None:
            return f"{symbol}0.00"
        return f"{symbol}{float(value):,.2f}"  # thousands separator, 2 decimals
    except (ValueError, TypeError):
        return f"{symbol}0.00"