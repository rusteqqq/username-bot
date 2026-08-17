import random
import string

VOWELS = set("aeiou")

# Красивые начала и слоги
GOOD_STARTS = (
    "ae", "al", "ar", "av",
    "el", "ev",
    "ia", "il", "ir",
    "la", "le", "li", "lo", "lu",
    "ma", "me", "mi", "mo",
    "na", "ne", "ni", "no", "nu",
    "ra", "re", "ri", "ro", "ru",
    "sa", "se", "si", "so",
    "ta", "te", "ti", "to",
    "va", "ve", "vi", "vo",
    "za", "ze", "zi", "zo",
)

GOOD_MIDDLES = (
    "la", "le", "li", "lo", "lu",
    "ra", "re", "ri", "ro", "ru",
    "na", "ne", "ni", "no", "nu",
    "va", "ve", "vi", "vo",
    "za", "ze", "zi", "zo",
    "sa", "se", "si", "so",
    "ta", "te", "ti", "to",
    "ma", "me", "mi", "mo",
    "el", "en", "er",
    "an", "ar", "av",
    "ia", "io",
)

GOOD_ENDS = (
    "a", "e", "i", "o", "u",
    "al", "an", "ar",
    "el", "en", "er",
    "ia", "io",
    "is", "on", "or",
    "us", "ix", "ex",
)

ROOTS = (
    "avel", "avero", "azur",
    "elva", "elora", "evra",
    "luna", "nexa", "navi",
    "nova", "novi", "orla",
    "vera", "veri", "vexa",
    "viro", "zena", "zora",
    "zuri", "lira", "livo",
    "mira", "milo", "nora",
    "niva", "riva", "rivo",
    "sela", "sora", "savi",
    "tavi", "vani", "vela",
    "velar", "zavel",
    "zelva", "zoria",
    "naver", "lurex", "virel",
)

# Плохие сочетания.
BAD_PAIRS = (
    "qq", "qx", "xq", "qz", "zq",
    "jq", "qj", "jx", "xj",
    "hx", "xh", "gx", "xg",
    "kx", "xk", "qh", "hq",
)

BAD_LETTERS = set("qx")


def is_valid_username(username):
    if not username:
        return False

    if not 5 <= len(username) <= 32:
        return False

    if not username.isascii():
        return False

    if not username.isalpha():
        return False

    return True


def looks_bad(username):
    username = username.lower()

    # Слишком много "тяжёлых" букв
    if sum(c in BAD_LETTERS for c in username) >= 2:
        return True

    # Плохие пары
    for pair in BAD_PAIRS:
        if pair in username:
            return True

    # Три согласные подряд
    consonants = 0

    for char in username:
        if char in VOWELS:
            consonants = 0
        else:
            consonants += 1

            if consonants >= 3:
                return True

    # Три гласные подряд тоже обычно выглядят плохо
    vowels = 0

    for char in username:
        if char in VOWELS:
            vowels += 1

            if vowels >= 3:
                return True
        else:
            vowels = 0

    return False


def natural_candidate(length):
    """
    Генерирует читаемый ник заданной длины.
    """

    # Сначала пробуем красивые корни
    if random.random() < 0.65:
        root = random.choice(ROOTS)

        if len(root) == length:
            return root

        if len(root) > length:
            candidate = root[:length]

            if is_valid_username(candidate) and not looks_bad(candidate):
                return candidate

        # Достраиваем короткий корень
        while len(root) < length:
            root += random.choice(GOOD_MIDDLES + GOOD_ENDS)

        candidate = root[:length]

        if is_valid_username(candidate) and not looks_bad(candidate):
            return candidate

    # Слоговая генерация
    result = ""

    while len(result) < length:
        if not result:
            chunk = random.choice(GOOD_STARTS)
        else:
            chunk = random.choice(GOOD_MIDDLES)

        result += chunk

    result = result[:length]

    if is_valid_username(result) and not looks_bad(result):
        return result

    # Запасной вариант CV/CVC
    result = ""

    consonants = "bcdfghklmnprstvz"
    vowels = "aeiou"

    for i in range(length):
        if i % 2 == 0:
            result += random.choice(consonants)
        else:
            result += random.choice(vowels)

    return result


def mask_candidate(mask):
    """
    Генерация по маске.
    ? = любая буква.
    """

    letters = string.ascii_lowercase

    result = ""

    for char in mask.lower():
        if char == "?":
            result += random.choice(letters)
        elif char in letters:
            result += char
        else:
            return None

    if not is_valid_username(result):
        return None

    return result


def generate_candidates(count=100, length=5, mask=None):
    """
    Генерирует много кандидатов для последующей проверки Telegram.

    count — сколько вернуть.
    length — длина ника.
    mask — например a?b?c.
    """

    if mask is not None:
        mask = mask.lower()

        if not 5 <= len(mask) <= 8:
            return []

        result = set()

        attempts = max(count * 100, 1000)

        for _ in range(attempts):
            candidate = mask_candidate(mask)

            if not candidate:
                continue

            if looks_bad(candidate):
                continue

            result.add(candidate)

            if len(result) >= count:
                break

        return list(result)

    if length not in (5, 6, 7, 8):
        return []

    result = set()

    attempts = max(count * 100, 1000)

    for _ in range(attempts):
        candidate = natural_candidate(length)

        if not candidate:
            continue

        if looks_bad(candidate):
            continue

        result.add(candidate.lower())

        if len(result) >= count:
            break

    return list(result)
