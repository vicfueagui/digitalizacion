import re

from django.core.exceptions import ValidationError

CURP_PATTERN = re.compile(r"^[A-Z0-9]{18}$")


def normalize_curp(value: str) -> str:
    return re.sub(r"\s+", "", (value or "")).upper()


def validate_curp(value: str) -> None:
    normalized = normalize_curp(value)
    if not CURP_PATTERN.fullmatch(normalized):
        raise ValidationError(
            "La CURP debe contener exactamente 18 caracteres alfanuméricos.",
            code="invalid_curp",
        )
