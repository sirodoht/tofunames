from django.core import validators as dj_validators
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


@deconstructible
class AlphanumericHyphenValidator(dj_validators.RegexValidator):
    regex = r"^[a-z\d-]+\Z"
    message = "Invalid value. Should include only lowercase letters, numbers, and -"
    flags = 0


@deconstructible
class HyphenOnlyValidator(dj_validators.RegexValidator):
    regex = r"^[-]*$"
    message = "Invalid value. Cannot be just hyphens."
    inverse_match = True
    flags = 0
