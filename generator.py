import random
from rating import rate_username

VOWELS = "aeiou"
COMMON_CONS = "bcdghklmnprst"
ACCENT_CONS = "fvwyzjxq"

# Фонетически приятные двухбуквенные куски.
SYLLABLES = [
    "ba", "be", "bi", "bo", "bu",
    "da", "de", "di", "do", "du",
    "fa", "fe", "fi", "fo", "fu",
    "ga", "ge", "gi", "go", "gu",
    "ka", "ke", "ki", "ko", "ku",
    "la", "le", "li", "lo", "lu",
    "ma", "me", "mi", "mo", "mu",
    "na", "ne", "ni", "no", "nu",
    "pa", "pe", "pi", "po", "pu",
    "ra", "re", "ri", "ro", "ru",
    "sa", "se", "si", "so", "su",
    "ta", "te", "ti", "to", "tu",
    "va", "ve", "vi", "vo", "vu",
    "za", "ze", "zi", "zo", "zu",
    "xe", "xi", "xo", "za", "ze",
]

# Готовые короткие формы помогают получать "брендовый" вид.
PATTERNS_5 = [
    "CVCVC", "CVCVV", "CVVCV", "VCVCV",
    "CVCCV", "CCVCV", "CVCVC"
]

def _pick_consonant():
    # Редкая буква появляется нечасто и только как акцент.
    if random.random() < 0.10:
        return random.choice(ACCENT_CONS)
    return random.choice(COMMON_CONS)


def _build_pattern(pattern):
    result = []
    for p in pattern:
        if p == "V":
            result.append(random.choice(VOWELS))
        elif p == "C":
            result.append(_pick_consonant())
    return "".join(result)


def _syllable_candidate(length):
    value = ""
    while len(value) < length:
        value += random.choice(SYLLABLES)

    value = value[:length]

    # Иногда добавляем один редкий акцент, но не делаем кашу.
    if length >= 5 and random.random() < 0.18:
        pos = random.choice([0, 1, 2, 3])
        value = value[:pos] + random.choice("zvxfj") + value[pos + 1:]

    return value


def _is_clean(u):
    if len(set(u)) < 3:
        return False

    # Не создаём явно мусорные последовательности.
    bad = (
        "qq", "xx", "qx", "xq", "qz", "zq",
        "xj", "jx", "qj", "jq"
    )
    if any(x in u for x in bad):
        return False

    # Не больше двух редких букв.
    if sum(c in "qzxj" for c in u) > 2:
        return False

    return True


def generate_candidates(count=120, length=5, mask=None):
    """
    Генерирует большой локальный пул, ранжирует его и возвращает
    только лучшие кандидаты. Telegram-запросов здесь нет.
    """

    target_pool = max(count * 80, 5000)
    candidates = set()

    if mask:
        # Для маски генерируем только допустимые варианты.
        for _ in range(target_pool):
            u = "".join(
                random.choice("abcdefghijklmnopqrstuvwxyz") if c == "?"
                else c.lower()
                for c in mask
            )

            if _is_clean(u):
                candidates.add(u)

        ranked = sorted(
            candidates,
            key=rate_username,
            reverse=True
        )
        return ranked[:count]

    for _ in range(target_pool):
        if length == 5:
            if random.random() < 0.65:
                u = _build_pattern(random.choice(PATTERNS_5))
            else:
                u = _syllable_candidate(length)
        else:
            u = _syllable_candidate(length)

        if len(u) == length and u.isalpha() and _is_clean(u):
            candidates.add(u)

    # Чем выше рейтинг — тем раньше scanner отправит ник Telegram.
    ranked = sorted(
        candidates,
        key=lambda x: (rate_username(x), random.random()),
        reverse=True
    )

    return ranked[:count]
