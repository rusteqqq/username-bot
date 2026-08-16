import re
from collections import Counter

VOWELS = set("aeiou")
RARE = set("qzx")
BAD_CLUSTERS = (
    "qq", "xx", "qz", "zq", "xq", "qx",
    "qj", "jq", "xj", "jx", "qv", "vq",
    "xv", "vx", "ww", "vv"
)

# Слова/последовательности, которые не хочется получать как "красивые" ники.
# Это не фильтр безопасности, а только фильтр качества.


def _letter_pattern(u):
    return "".join("V" if c in VOWELS else "C" for c in u if c.isalpha())


def _syllable_score(u):
    pattern = _letter_pattern(u)
    good = {
        "CVCVC", "CVCCV", "CVVCV", "VCVCV",
        "CVCVV", "CVVCC", "CVVCVC", "CVCVCV"
    }
    if pattern in good:
        return 1.0
    if "CCC" in pattern or "VVV" in pattern:
        return -1.2
    return 0.0


def rate_username(username):
    u = username.lower().lstrip("@")

    if not re.fullmatch(r"[a-z0-9_]+", u):
        return 0.0


    score = 5.0

    # Длина: 4–5 особенно интересны.
    if len(u) == 4:
        score += 2.7
    elif len(u) == 5:
        score += 2.2
    elif len(u) == 6:
        score += 1.0
    elif len(u) == 7:
        score += 0.2
    else:
        score -= min(2.5, (len(u) - 7) * 0.4)

    if "_" in u:
        score -= 2.0
    if any(c.isdigit() for c in u):
        score -= 2.0

    if len(set(u)) == len(u):
        score += 0.55

    # Хорошее чередование согласных/гласных.
    score += _syllable_score(u)

    # Слишком много редких букв выглядит как рандом.
    rare_count = sum(c in RARE for c in u)
    if rare_count == 0:
        score += 0.25
    elif rare_count == 1:
        score += 0.35
    elif rare_count == 2:
        score -= 0.35
    else:
        score -= 1.5

    # q/x/z/v допустимы, но не подряд.
    if any(cluster in u for cluster in BAD_CLUSTERS):
        score -= 2.0

    # Начало/конец, которые легко произнести.
    if u[0] in VOWELS:
        score += 0.15
    if u[-1] in VOWELS:
        score += 0.35

    # Бонус за "брендовый" вид: одна редкая буква + обычная фонетика.
    if rare_count == 1 and _syllable_score(u) > 0:
        score += 0.35

    # Повтор одной буквы максимум один раз.
    counts = Counter(u)
    if max(counts.values()) >= 3:
        score -= 1.0

    return round(max(0.0, min(10.0, score)), 1)
