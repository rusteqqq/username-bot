def estimate_price(rating, length):
    # Ориентировочная эвристика. Не является гарантией цены продажи.
    if length == 4:
        multiplier = 4.0
    elif length == 5:
        multiplier = 2.0
    elif length <= 7:
        multiplier = 1.2
    else:
        multiplier = 0.8

    base = max(1.0, rating * multiplier)
    return round(base * 0.7, 2), round(base * 1.4, 2)
