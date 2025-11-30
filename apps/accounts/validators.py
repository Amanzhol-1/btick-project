from django.core.exceptions import ValidationError


# Restricted email domains (can be expanded)
_RESTRICTED_DOMAINS = ('mail.ru', 'tempmail.com')


def validate_email_domain(email: str) -> None:
    """
    Validates that email does not use restricted domains.

    Args:
        email: The email address to validate.

    Raises:
        ValidationError: If email domain is in restricted list.
    """
    domain = email.split('@')[-1].lower()
    if domain in _RESTRICTED_DOMAINS:
        raise ValidationError(
            f'Email domain "{domain}" is not allowed.'
        )


def validate_email_not_in_name(email: str, full_name: str) -> None:
    """
    Validates email local part doesn't appear in full name.

    Args:
        email: The email address to validate.
        full_name: The user's full name to check against.

    Raises:
        ValidationError: If email username appears in full name.
    """
    if not email or not full_name:
        return
    local_part = email.split('@')[0].lower()
    if local_part in full_name.lower():
        raise ValidationError(
            'Email username should not be part of your name.'
        )
