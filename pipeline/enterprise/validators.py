from datetime import datetime


def is_valid_date_ddmmyyyy(value: str) -> bool:
    if not value:
        return True
    try:
        datetime.strptime(value, "%d/%m/%Y")
        return True
    except ValueError:
        return False


def is_valid_nhs_number(value: str) -> bool:
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) != 10:
        return False
    base9 = digits[:9]
    check = int(digits[9])
    total = 0
    for idx, ch in enumerate(base9):
        total += int(ch) * (10 - idx)
    rem = total % 11
    expected = 11 - rem
    if expected == 11:
        expected = 0
    if expected == 10:
        return False
    return check == expected

