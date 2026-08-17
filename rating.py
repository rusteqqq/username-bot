VOWELS = set("aeiou")

BAD_LETTERS = set("qx")

GOOD_PAIRS = {
    "ae", "al", "ar", "av",
    "el", "ev",
    "ia", "ie", "il", "ir", "io",
    "la", "le", "li", "lo", "lu",
    "ma", "me", "mi", "mo", "mu",
    "na", "ne", "ni", "no", "nu",
    "ra", "re", "ri", "ro", "ru",
    "sa", "se", "si", "so", "su",
    "ta", "te", "ti", "to", "tu",
    "va", "ve", "vi", "vo", "vu",
    "za", "ze", "zi", "zo", "zu",
}

BAD_PAIRS = {
    "qq", "qx", "xq", "qz", "zq",
    "jq", "qj", "jx", "xj",
    "hx", "xh", "gx", "xg",
    "kx", "xk", "qh", "hq",
    "bh", "hb", "ph", "hp",
    "vh", "hv", "dh", "hd",
    "cb", "bc", "cp", "pc",
}


def _clamp(value):
    return max(0.0, min(10.0, value))


def is_bad_username(username):
    username = username.lower()

    # q и x полностью запрещаем для обычного генератора
    if any(char in BAD_LETTERS for char in username):
        return True

    # Плохие пары
    for pair in BAD_PAIRS:
        if pair in username:
            return True

    # 3 согласные подряд
    consonants = 0

    for char in username:
        if char in VOWELS:
            consonants = 0
        else:
            consonants += 1

            if consonants >= 3:
                return True

    # 3 гласные подряд
    vowels = 0

    for char in username:
        if char in VOWELS:
            vowels += 1

            if vowels >= 3:
                return True
        else:
            vowels = 0

    return False


def rate_username(username):
    username = username.lower().strip()

    if not username.isascii() or not username.isalpha():
        return 0.0

    if not 5 <= len(username) <= 8:
        return 0.0

    # Мусор сразу получает 0
    if is_bad_username(username):
        return 0.0

    score = 5.0

    # Чередование согласная/гласная
    transitions = 0

    for a, b in zip(username, username[1:]):
        if (a in VOWELS) != (b in VOWELS):
            transitions += 1

    ratio = transitions / max(1, len(username) - 1)

    if ratio >= 0.75:
        score += 2.0
    elif ratio >= 0.60:
        score += 1.3
    elif ratio >= 0.45:
        score += 0.5
    else:
        score -= 1.5

    # Красивые пары
    for i in range(len(username) - 1):
        pair = username[i:i + 2]

        if pair in GOOD_PAIRS:
            score += 0.3

    # Красивые окончания
    if username.endswith((
        "a", "e", "i", "o",
        "ia", "ie", "io",
        "al", "el", "er",
        "an", "ar", "en", "in",
        "on", "or"
    )):
        score += 0.6

    # Короткие ники ценнее
    if len(username) == 5:
        score += 1.3
    elif len(username) == 6:
        score += 0.9
    elif len(username) == 7:
        score += 0.5

    # Повторы
    repeated = sum(
        1 for a, b in zip(username, username[1:])
        if a == b
    )

    if repeated == 1:
        score += 0.1
    elif repeated >= 2:
        score -= 1.0

    return round(_clamp(score), 1)


def get_rating(username):
    return rate_username(username)
