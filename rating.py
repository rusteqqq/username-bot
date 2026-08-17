VOWELS = set("aeiou")

# Красивые пары получают дополнительный вес
GOOD_PAIRS = {
    "ae", "al", "ar", "av",
    "el", "ev",
    "ia", "il", "ir", "io",
    "la", "le", "li", "lo", "lu",
    "ma", "me", "mi", "mo",
    "na", "ne", "ni", "no", "nu",
    "ra", "re", "ri", "ro", "ru",
    "sa", "se", "si", "so",
    "ta", "te", "ti", "to",
    "va", "ve", "vi", "vo",
    "za", "ze", "zi", "zo",
}

BAD_PAIRS = {
    "qq", "qx", "xq", "qz", "zq",
    "jq", "qj", "jx", "xj",
    "hx", "xh", "gx", "xg",
    "kx", "xk", "qh", "hq",
}


def _clamp(value, minimum=0.0, maximum=10.0):
    return max(minimum, min(maximum, value))


def _pronounceability(username):
    """
    Оценивает насколько ник похож на нормальное
    произносимое слово.
    """

    score = 5.0

    username = username.lower()

    # Чередование согласных/гласных
    transitions = 0

    for a, b in zip(username, username[1:]):
        if (a in VOWELS) != (b in VOWELS):
            transitions += 1

    if len(username) > 1:
        ratio = transitions / (len(username) - 1)

        if ratio >= 0.65:
            score += 2.2
        elif ratio >= 0.5:
            score += 1.2
        elif ratio < 0.3:
            score -= 1.8

    # Красивые пары
    for i in range(len(username) - 1):
        pair = username[i:i + 2]

        if pair in GOOD_PAIRS:
            score += 0.35

        if pair in BAD_PAIRS:
            score -= 2.0

    # Три согласные подряд
    for i in range(len(username) - 2):
        part = username[i:i + 3]

        if all(c not in VOWELS for c in part):
            score -= 2.5

    # Три гласные подряд
    for i in range(len(username) - 2):
        part = username[i:i + 3]

        if all(c in VOWELS for c in part):
            score -= 1.5

    return _clamp(score)


def rate_username(username):
    """
    Основной рейтинг ника 0–10.

    Важно:
    это рейтинг КРАСИВОЙ/ЛИКВИДНОЙ формы,
    а не гарантия реальной рыночной цены.
    """

    username = username.lower().strip()

    if not username.isascii() or not username.isalpha():
        return 0.0

    if not 5 <= len(username) <= 32:
        return 0.0

    score = _pronounceability(username)

    # Короткие ники ценнее при прочих равных
    length_bonus = {
        5: 1.4,
        6: 0.9,
        7: 0.5,
        8: 0.2,
    }.get(len(username), 0.0)

    score += length_bonus

    # Повтор букв может быть красивым, но не слишком часто
    repeated = 0

    for a, b in zip(username, username[1:]):
        if a == b:
            repeated += 1

    if repeated == 1:
        score += 0.2
    elif repeated >= 2:
        score -= 0.8

    # Слишком много редких тяжёлых букв
    heavy = sum(c in "qxjx" for c in username)

    if heavy == 1:
        score -= 0.8
    elif heavy >= 2:
        score -= 2.5

    # Симметричные/приятные окончания
    if username.endswith(
        ("a", "e", "i", "o", "ia", "io", "el", "er", "en", "ar")
    ):
        score += 0.5

    return round(_clamp(score), 1)


def get_rating(username):
    return rate_username(username)
